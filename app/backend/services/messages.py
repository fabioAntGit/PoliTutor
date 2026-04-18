from rag.src.retrieval import ask
from app.backend.repositories.chats import ChatRepository
from app.backend.core.exceptions import ChatNotFoundError
from app.backend.repositories.messages import MessageRepository
from app.backend.schemas.message.models import Message, Source
from app.backend.schemas.message.response import MessageResponse
from app.backend.services.interfaces.message_service import IMessageService


class MessageService(IMessageService):
    def __init__(
        self,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
    ) -> None:
        self.message_repository = message_repository
        self.chat_repository = chat_repository

    async def send_message(
        self, 
        conversation_id: str,
        question: str,
        iaedu_endpoint: str,
        iaedu_api_key: str,
        iaedu_channel_id: str
    ) -> MessageResponse:
        conversation = await self.chat_repository.get_chat(conversation_id)

        if conversation is None:
            raise ChatNotFoundError(conversation_id)

        await self.message_repository.create(
            Message(conversation_id=conversation_id, role="user", content=question)
        )

        response = ask(
            conversation.course,
            question,
            iaedu_url=iaedu_endpoint,
            iaedu_channel_id=iaedu_channel_id,
            iaedu_api_key=iaedu_api_key,
        )

        await self.message_repository.create(
            Message(
                conversation_id=conversation_id,
                role="assistant",
                content=response.answer,
                sources=[Source(filename=source.filename, pages=source.pages) for source in response.sources],
            )
        )

        return MessageResponse(
            answer=response.answer,
            sources=[Source(filename=s.filename, pages=s.pages) for s in response.sources],
            is_fallback=response.is_fallback,
            guardrail_triggered=response.guardrail_triggered,
        )

    async def get_chat_messages(self, conversation_id: str) -> list[Message]:
        return await self.message_repository.get_messages(conversation_id)
