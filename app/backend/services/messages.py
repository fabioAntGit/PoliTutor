import asyncio
import importlib.util
import logging
import sys
from pathlib import Path

from rag.src.shared.models import IaEduCredentials, TutorResponse
from rag.src.runtime.retrieval import ask
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.core.exceptions import ChatNotFoundError, AccessDeniedError
from app.backend.core.projects import PROJECT_REGISTRY
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.repositories.interfaces.redis_repository import IRedisRepository
from app.backend.schemas.message.models import Message, Source
from app.backend.schemas.message.response import MessageResponse
from app.backend.services.interfaces.message_service import IMessageService
from app.backend.services.interfaces.context_service import IContextService
from app.backend.services.interfaces.user_memory_service import IUserMemoryService

logger = logging.getLogger(__name__)

_DYNAMIC_GR_LLM = "openrouter_gemini25"
_DYNAMIC_GR_STRICTNESS = 70
_DYNAMIC_GR_MODULE = None
_DYNAMIC_GR_ROOT: Path | None = None


def _load_dynamic_guardrail_runner():
    global _DYNAMIC_GR_MODULE, _DYNAMIC_GR_ROOT

    if _DYNAMIC_GR_MODULE is not None and _DYNAMIC_GR_ROOT is not None:
        return _DYNAMIC_GR_MODULE.run_workflow, _DYNAMIC_GR_ROOT

    dynamic_gr_root = Path(__file__).resolve().parents[3] / "DynamicGr"
    if str(dynamic_gr_root) not in sys.path:
        sys.path.append(str(dynamic_gr_root))

    module_path = dynamic_gr_root / "main.py"
    spec = importlib.util.spec_from_file_location(
        "dynamicgr_main", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("DynamicGr main module could not be loaded.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    _DYNAMIC_GR_MODULE = module
    _DYNAMIC_GR_ROOT = dynamic_gr_root
    return module.run_workflow, dynamic_gr_root


async def _run_dynamic_guardrail(prompt: str, project_name: str) -> tuple[bool, list[str]]:
    run_workflow, dynamic_gr_root = _load_dynamic_guardrail_runner()
    context_path = dynamic_gr_root / "projects" / "projects_context" / f"{project_name}.json"

    output = await run_workflow(
        prompt=prompt,
        context_file=str(context_path),
        llm_name=_DYNAMIC_GR_LLM,
        strictness=_DYNAMIC_GR_STRICTNESS,
    )

    return output.get("is_allowed", True), output.get("rejection_reasons", [])


class MessageService(IMessageService):
    def __init__(
        self,
        message_repository: IMessageRepository,
        chat_repository: IChatRepository,
        redis_repository: IRedisRepository,
        context_service: IContextService,
        user_memory_service: IUserMemoryService,
    ) -> None:
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.redis_repository = redis_repository
        self.context_service = context_service
        self.user_memory_service = user_memory_service

    async def _handle_dynamic_source(
        self,
        question: str,
        project_config,
        conversation,
        summary,
        history,
        iaedu_creds,
        memory_context: str,
    ) -> TutorResponse:
        """Runs the dynamic guardrail and, if allowed, delegates to RAG."""
        logger.info(
            "DynamicGr guardrail enabled for project_id=%s name=%s",
            conversation.project_id,
            project_config.name,
        )
        is_allowed, rejection_reasons = await _run_dynamic_guardrail(
            question,
            project_config.name,
        )
        if not is_allowed:
            logger.info("DynamicGr blocked prompt: %s", rejection_reasons)
            reason_text = "; ".join([r for r in rejection_reasons if r])
            return TutorResponse(
                answer=reason_text or "Prompt blocked by guardrail.",
                sources=[],
                is_fallback=True,
                is_guardrail=True,
            )

        logger.info("DynamicGr allowed prompt; returning guardrail response.")
        # Note: We return a non-blocking response here to provide immediate feedback to the user.
        return TutorResponse(
            answer="The response is not blocked",
            sources=[],
            is_fallback=False,
            is_guardrail=False,
        )

    async def send_message(
        self,
        conversation_id: str,
        question: str,
        iaedu_endpoint: str,
        iaedu_api_key: str,
        iaedu_channel_id: str,
    ) -> MessageResponse:
        conversation = await self.chat_repository.get_chat(conversation_id)

        if conversation is None:
            raise ChatNotFoundError(conversation_id)

        if conversation.user_id != iaedu_channel_id:
            raise AccessDeniedError(
                "Nao tens permissao para enviar mensagens para este chat.")

        summary, history = await self.context_service.get_or_load_context(conversation_id)

        memory_context = await self.user_memory_service.get_context_for_prompt(
            conversation.user_id, conversation.course
        )

        user_msg = Message(conversation_id=conversation_id,
                           role="user", content=question)
        user_msg.id = await self.message_repository.create(user_msg)
        await self.redis_repository.add_message(user_msg)

        iaedu_creds = IaEduCredentials(
            url=iaedu_endpoint,
            channel_id=iaedu_channel_id,
            api_key=iaedu_api_key,
        )

        project_config = PROJECT_REGISTRY.get(conversation.project_id)

        if project_config is not None and project_config.source == "Dynamic":
            response: TutorResponse = await self._handle_dynamic_source(
                question,
                project_config,
                conversation,
                summary,
                history,
                iaedu_creds,
                memory_context or "",
            )
        else:
            if project_config is None:
                logger.info("Project config missing for project_id=%s",
                            conversation.project_id)
            else:
                logger.info(
                    "DynamicGr disabled for project_id=%s source=%s",
                    conversation.project_id,
                    project_config.source,
                )
            response = await asyncio.to_thread(
                ask,
                conversation.course,
                question,
                summary,
                history,
                iaedu_creds,
                memory_context or "",
            )

        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.answer,
            sources=[Source(filename=s.filename, pages=s.pages)
                     for s in response.sources],
        )
        assistant_msg.id = await self.message_repository.create(assistant_msg)
        await self.redis_repository.add_message(assistant_msg)

        await self.context_service.check_and_trigger_summary(
            conversation_id, conversation.user_id, conversation.course
        )

        return MessageResponse(
            user_message_id=str(user_msg.id),
            assistant_message_id=str(assistant_msg.id),
            answer=response.answer,
            sources=[Source(filename=s.filename, pages=s.pages)
                     for s in response.sources],
            is_fallback=response.is_fallback,
            guardrail_triggered=response.is_guardrail or response.is_output_guardrail,
        )

    async def get_chat_messages(self, conversation_id: str) -> list[Message]:
        return await self.message_repository.get_messages(conversation_id)
