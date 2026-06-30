import asyncio

from contracts.rag.interfaces import IRagEngine
from contracts.rag.models import TutorResponse, TutorSource
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.core.exceptions import AccessDeniedError, NotFoundError
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.repositories.interfaces.cache_repository import ICacheRepository
from app.backend.schemas.message.models import Message, Source
from app.backend.services.interfaces.message_service import IMessageService
from app.backend.services.interfaces.context_service import IContextService
from app.backend.services.interfaces.user_memory_service import IUserMemoryService


class MessageService(IMessageService):
    def __init__(
        self,
        message_repository: IMessageRepository,
        chat_repository: IChatRepository,
        course_repository: ICourseRepository,
        cache_repository: ICacheRepository,
        context_service: IContextService,
        user_memory_service: IUserMemoryService,
        rag_engine: IRagEngine,
    ) -> None:
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.course_repository = course_repository
        self.cache_repository = cache_repository
        self.context_service = context_service
        self.user_memory_service = user_memory_service
        self.rag_engine = rag_engine

    async def send_message(
        self,
        conversation_id: str,
        question: str,
        user_id: str,
    ) -> tuple[Message, Message, TutorResponse]:
        conversation = await self.chat_repository.get_chat(conversation_id)

        if conversation is None:
            raise NotFoundError(
                message="Chat nao encontrado",
                code="chat_not_found",
                details={"conversation_id": conversation_id},
            )

        if conversation.user_id != user_id:
            raise AccessDeniedError(message="Nao tens permissao para enviar mensagens para este chat.")

        course = await self.course_repository.find_by_id(conversation.course_id)
        if course is None:
            raise NotFoundError(
                message="Cadeira nao encontrada",
                code="course_not_found",
                details={"course_id": conversation.course_id},
            )

        summary, history = await self.context_service.get_or_load_context(conversation_id)

        memory_context = await self.user_memory_service.get_context_for_prompt(
            conversation.user_id, conversation.course_id
        )

        user_msg = Message(conversation_id=conversation_id, role="user", content=question)
        user_msg.id = await self.message_repository.create(user_msg)

        response = await asyncio.to_thread(
            self.rag_engine.ask,
            course.code,
            question,
            summary,
            history,
            memory_context or "",
        )

        backend_response = TutorResponse(
            answer=response.answer,
            sources=[TutorSource(filename=s.filename, pages=s.pages) for s in response.sources],
            is_fallback=response.is_fallback,
            is_guardrail=response.is_guardrail,
            is_output_guardrail=response.is_output_guardrail,
            is_retrieval_fallback=response.is_retrieval_fallback
        )

        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=backend_response.answer,
            sources=[Source(filename=source.filename, pages=source.pages) for source in backend_response.sources],
        )

        assistant_msg.id = await self.message_repository.create(assistant_msg)

        await self.cache_repository.add_message(user_msg)
        await self.cache_repository.add_message(assistant_msg)

        await self.chat_repository.touch(conversation_id)

        await self.context_service.check_and_trigger_summary(
            conversation_id, conversation.user_id, conversation.course_id
        )

        return user_msg, assistant_msg, backend_response
