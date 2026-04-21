from rag.src.shared.models import IaEduCredentials
from rag.src.runtime.retrieval import ask
from app.backend.repositories.chats import ChatRepository
from app.backend.core.exceptions import ChatNotFoundError
from app.backend.repositories.messages import MessageRepository
from app.backend.repositories.redis import RedisRepository
from app.backend.schemas.message.models import Message, Source
from app.backend.schemas.message.response import MessageResponse
from app.backend.services.interfaces.message_service import IMessageService


from app.backend.services.interfaces.context_service import IContextService

class MessageService(IMessageService):
    def __init__(
        self,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        redis_repository: RedisRepository,
        context_service: IContextService,
    ) -> None:
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.redis_repository = redis_repository
        self.context_service = context_service

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

        user_msg = Message(conversation_id=conversation_id, role="user", content=question)

        await self.message_repository.create(user_msg)
        await self.redis_repository.add_message(user_msg)

        summary, messages = await self.context_service.get_or_load_context(conversation_id)

        iaedu_creds = IaEduCredentials(
            url=iaedu_endpoint,
            channel_id=iaedu_channel_id,
            api_key=iaedu_api_key
        )

        response = ask(
            conversation.course,
            question,
            summary,
            messages,
            iaedu_creds=iaedu_creds,
        )

        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.answer,
            sources=[Source(filename=source.filename, pages=source.pages) for source in response.sources],
        )

        await self.message_repository.create(assistant_msg)
        await self.redis_repository.add_message(assistant_msg)

        await self.context_service.check_and_trigger_summary(conversation_id)

        return MessageResponse(
            answer=response.answer,
            sources=[Source(filename=s.filename, pages=s.pages) for s in response.sources],
            is_fallback=response.is_fallback,
            guardrail_triggered=response.is_guardrail or response.is_output_guardrail,
        )

    async def get_chat_messages(self, conversation_id: str) -> list[Message]:
        return await self.message_repository.get_messages(conversation_id)
