from app.backend.repositories.chats import ChatRepository
from app.backend.repositories.messages import MessageRepository
from app.backend.repositories.redis import RedisRepository
from app.backend.schemas.message.models import Message
from app.backend.services.interfaces.context_service import IContextService

class ContextService(IContextService):
    def __init__(
        self,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        redis_repository: RedisRepository,
    ) -> None:
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.redis_repository = redis_repository

    async def get_or_load_context (self, conversation_id: str) -> tuple[str | None, str]:
        summary, messages = await self.redis_repository.get_context(conversation_id)
        
        if not messages:
            summary = await self.chat_repository.get_summary(conversation_id)
            messages = await self.message_repository.get_recent_messages(conversation_id, limit=16)
            
            last_summ_id = await self.chat_repository.get_last_summarized_message_id(conversation_id)
            count = await self.message_repository.get_number_of_messages_after_summary(conversation_id, last_summ_id)
            await self.redis_repository.set_message_count(conversation_id, count)
            
            if summary:
                await self.redis_repository.set_summary(conversation_id, summary)
            
            if messages:
                await self.redis_repository.repopulate_messages(conversation_id, messages)
        
        return summary, self._format_history(messages)

    async def check_and_trigger_summary(self, conversation_id: str) -> None:
        count = await self.redis_repository.get_message_count(conversation_id)
        
        if count >= 16:
            summary, messages = await self.redis_repository.get_context(conversation_id)
            
            # TODO chamar o OpenRouter (método a ser criado futuramente)
            # new_summary = await self.llm_service.call_openrouter(summary, messages)
            new_summary = "TODO: Substituir pela resposta do OpenRouter"
            
            if messages:
                last_msg_id = messages[-1].id
                await self.chat_repository.set_summary(conversation_id, new_summary, last_msg_id)
                await self.redis_repository.set_summary(conversation_id, new_summary)
            
            await self.redis_repository.reset_message_count(conversation_id)

    def _format_history(self, messages: list[Message]) -> str:
        history_lines = []
        for msg in messages:
            role = "Student" if msg.role == "user" else "Tutor"
            history_lines.append(f"{role}: {msg.content}")
        return "\n".join(history_lines)
