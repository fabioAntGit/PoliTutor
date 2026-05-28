import asyncio

from rag.src.runtime.retrieval import ask
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.core.exceptions import ChatNotFoundError, AccessDeniedError
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.repositories.interfaces.redis_repository import IRedisRepository
from app.backend.schemas.message.models import Message, Source
from app.backend.schemas.message.response import MessageResponse
from app.backend.services.interfaces.message_service import IMessageService
from app.backend.services.interfaces.context_service import IContextService
from app.backend.services.interfaces.user_memory_service import IUserMemoryService


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

    async def send_message(
        self,
        conversation_id: str,
        question: str,
        user_id: str,
    ) -> MessageResponse:
        conversation = await self.chat_repository.get_chat(conversation_id)

        if conversation is None:
            raise ChatNotFoundError(conversation_id)

        if conversation.user_id != user_id:
            raise AccessDeniedError("Nao tens permissao para enviar mensagens para este chat.")

        summary, history = await self.context_service.get_or_load_context(conversation_id)

        # Enrich summary with semantically relevant long-term memories
        memory_context = await self.user_memory_service.get_context_for_prompt(
            conversation.user_id, conversation.course
        )

        response = await asyncio.to_thread(
            ask,
            conversation.course,
            question,
            summary,
            history,
            None,
            memory_context or "",
        )

        user_msg = Message(conversation_id=conversation_id, role="user", content=question)
        user_msg.id = await self.message_repository.create(user_msg)
        await self.redis_repository.add_message(user_msg)

        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.answer,
            sources=[Source(filename=source.filename, pages=source.pages) for source in response.sources],
        )

        assistant_msg.id = await self.message_repository.create(assistant_msg)
        await self.redis_repository.add_message(assistant_msg)

        await self.chat_repository.touch(conversation_id)

        await self.context_service.check_and_trigger_summary(
            conversation_id, conversation.user_id, conversation.course
        )

        return MessageResponse(
            user_message_id=str(user_msg.id),
            assistant_message_id=str(assistant_msg.id),
            answer=response.answer,
            sources=[Source(filename=s.filename, pages=s.pages) for s in response.sources],
            is_fallback=response.is_fallback,
            guardrail_triggered=response.is_guardrail or response.is_output_guardrail,
        )

    async def get_chat_messages(self, conversation_id: str) -> list[Message]:
        return await self.message_repository.get_messages(conversation_id)
