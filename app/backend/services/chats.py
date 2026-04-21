from app.backend.core.exceptions import (
    ChatNotFoundError,
    ProjectNotFoundError,
)
from app.backend.repositories.chats import ChatRepository
from app.backend.repositories.messages import MessageRepository
from app.backend.repositories.redis import RedisRepository
from app.backend.repositories.projects import PROJECT_REGISTRY
from app.backend.schemas.chat.models import Chat
from app.backend.schemas.chat.response import ChatRead, ChatCreated
from app.backend.services.interfaces.chat_service import IChatService
from app.backend.services.interfaces.message_service import IMessageService


class ChatService(IChatService):
    def __init__(
        self,
        chat_repository: ChatRepository,
        message_repository: MessageRepository,
        redis_repository: RedisRepository,
        message_service: IMessageService,
    ) -> None:
        self.chat_repository = chat_repository
        self.message_repository = message_repository
        self.redis_repository = redis_repository
        self.message_service = message_service

    async def create_chat(self, project_id: str, user_id: str) -> tuple[ChatCreated, bool]:
        project_config = PROJECT_REGISTRY.get(project_id)

        if project_config is None:
            raise ProjectNotFoundError(project_id)

        existing_chat = await self.chat_repository.get_chat_by_project_and_user(
            project_id, user_id
        )

        if existing_chat is not None:
            return ChatCreated(conversation_id=existing_chat.conversation_id), False

        chat = Chat(
            project_id=project_id,
            course=project_config.course_code,
            user_id=user_id,
        )

        conversation_id = await self.chat_repository.create(chat)
        return ChatCreated(conversation_id=conversation_id), True

    async def get_chat(self, conversation_id: str) -> ChatRead:
        chat = await self.chat_repository.get_chat(conversation_id)

        if chat is None:
            raise ChatNotFoundError(conversation_id)

        project_config = PROJECT_REGISTRY.get(chat.project_id)
        
        if project_config is None:
            raise ProjectNotFoundError(chat.project_id)

        messages = await self.message_service.get_chat_messages(conversation_id)

        return ChatRead(
            conversation_id=chat.conversation_id,
            project_id=chat.project_id,
            project_name=project_config.name,
            user_id=chat.user_id,
            summary=chat.summary,
            messages=messages,
        )
