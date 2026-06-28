import asyncio
import logging
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.repositories.interfaces.cache_repository import ICacheRepository
from app.backend.schemas.message.models import Message
from app.backend.services.interfaces.context_service import IContextService
from app.backend.services.interfaces.user_memory_service import IUserMemoryService
from app.backend.core.background import run_in_background
from app.backend.gateways.interfaces.model_client import IModelClient
from app.backend.core.config import SUMMARIZATION_PROMPT, SUMMARIZATION_THRESHOLD, OPENROUTER_MODEL_SUMMARIZATION

logger = logging.getLogger(__name__)

class ContextService(IContextService):
    def __init__(
        self,
        message_repository: IMessageRepository,
        chat_repository: IChatRepository,
        cache_repository: ICacheRepository,
        user_memory_service: IUserMemoryService,
        model_client: IModelClient,
    ) -> None:
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.cache_repository = cache_repository
        self.user_memory_service = user_memory_service
        self.model_client = model_client

    async def get_or_load_context(self, conversation_id: str) -> tuple[str | None, list[dict]]:
        summary, messages = await self.cache_repository.get_context(conversation_id)

        if not messages:
            summary = await self.chat_repository.get_summary(conversation_id)
            messages = await self.message_repository.get_recent_messages(conversation_id, limit=16)

            last_summ_id = await self.chat_repository.get_last_summarized_message_id(conversation_id)
            count = await self.message_repository.get_number_of_messages_after_summary(conversation_id, last_summ_id)
            await self.cache_repository.set_message_count(conversation_id, count)

            if summary:
                await self.cache_repository.set_summary(conversation_id, summary)

            if messages:
                await self.cache_repository.repopulate_messages(conversation_id, messages)

        return summary, self._format_history_structured(messages)

    async def check_and_trigger_summary(self, conversation_id: str, user_id: str, course: str) -> None:
        count = await self.cache_repository.get_message_count(conversation_id)
        if count < SUMMARIZATION_THRESHOLD:
            return

        has_lock = await self.cache_repository.acquire_summary_lock(conversation_id)
        if not has_lock:
            logger.info("Summary already running for conversation %s", conversation_id)
            return

        summary_old, messages = await self.cache_repository.get_context(conversation_id)
        if not messages:
            await self.cache_repository.release_summary_lock(conversation_id)
            return

        logger.info("Triggering background summary for conversation %s (count=%d)", conversation_id, count)
        run_in_background(self._summarize(conversation_id, user_id, course, summary_old, messages))

    async def _summarize(
        self,
        conversation_id: str,
        user_id: str,
        course: str,
        summary_old: str | None,
        messages: list[Message],
    ) -> None:
        try:
            prompt = SUMMARIZATION_PROMPT.format(
                old_summary=summary_old or "Não existe resumo anterior.",
                history=self._format_history(messages),
            )
            new_summary = await asyncio.to_thread(
                self.model_client.call,
                [{"role": "user", "content": prompt}],
                model=OPENROUTER_MODEL_SUMMARIZATION,
            )

            if not new_summary:
                logger.warning("OpenRouter returned empty summary for conversation %s", conversation_id)
                return
                

            await self.chat_repository.set_summary(conversation_id, new_summary, messages[-1].id)
            await self.cache_repository.set_summary(conversation_id, new_summary)
            await self.cache_repository.trim_messages(conversation_id, limit=16)
            await self.cache_repository.reset_message_count(conversation_id)
            logger.info("Summary updated for conversation %s", conversation_id)

            run_in_background(self.user_memory_service.extract_and_upsert(user_id, course, new_summary))
        except Exception as e:
            logger.error("Failed to generate summary for conversation %s: %s", conversation_id, e)
        finally:
            await self.cache_repository.release_summary_lock(conversation_id)

    def _format_history(self, messages: list[Message]) -> str:
        history_lines = []
        for msg in messages:
            role = "Student" if msg.role == "user" else "Tutor"
            history_lines.append(f"{role}: {msg.content}")
        return "\n".join(history_lines)

    def _format_history_structured(self, messages: list[Message]) -> list[dict]:
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]
