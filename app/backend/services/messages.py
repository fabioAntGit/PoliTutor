from rag.src.shared.models import IaEduCredentials
from rag.src.runtime.retrieval import ask
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.core.exceptions import ChatNotFoundError, AccessDeniedError
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.repositories.interfaces.redis_repository import IRedisRepository
from app.backend.schemas.message.models import Message, Source
from app.backend.schemas.message.response import MessageResponse
from app.backend.services.interfaces.message_service import IMessageService


from app.backend.services.interfaces.context_service import IContextService

class MessageService(IMessageService):
    def __init__(
        self,
        message_repository: IMessageRepository,
        chat_repository: IChatRepository,
        redis_repository: IRedisRepository,
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

        if conversation.user_id != iaedu_channel_id:
            raise AccessDeniedError("Nao tens permissao para enviar mensagens para este chat.")

        summary, history = await self.context_service.get_or_load_context(conversation_id)

        user_msg = Message(conversation_id=conversation_id, role="user", content=question)

        user_msg.id = await self.message_repository.create(user_msg)
        await self.redis_repository.add_message(user_msg)

        iaedu_creds = IaEduCredentials(
            url=iaedu_endpoint,
            channel_id=iaedu_channel_id,
            api_key=iaedu_api_key
        )

        response = ask(
            conversation.course,
            question,
            summary,
            history,
            iaedu_creds=iaedu_creds,
        )

        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=response.answer,
            sources=[Source(filename=source.filename, pages=source.pages) for source in response.sources],
        )

        assistant_msg.id = await self.message_repository.create(assistant_msg)
        await self.redis_repository.add_message(assistant_msg)

        await self.context_service.check_and_trigger_summary(conversation_id)

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
