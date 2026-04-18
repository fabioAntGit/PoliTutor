from fastapi import Depends

from app.backend.repositories.chats import ChatRepository
from app.backend.repositories.messages import MessageRepository
from app.backend.services.chats import ChatService
from app.backend.services.messages import MessageService
from app.backend.services.projects import ProjectService
from app.backend.services.interfaces.chat_service import IChatService
from app.backend.services.interfaces.message_service import IMessageService
from app.backend.services.interfaces.project_service import IProjectService


def get_chat_repository() -> ChatRepository:
    return ChatRepository()


def get_message_repository() -> MessageRepository:
    return MessageRepository()


def get_message_service(
    message_repository: MessageRepository = Depends(get_message_repository),
    chat_repository: ChatRepository = Depends(get_chat_repository),
) -> IMessageService:
    return MessageService(
        message_repository=message_repository,
        chat_repository=chat_repository,
    )


def get_chat_service(
    chat_repository: ChatRepository = Depends(get_chat_repository),
    message_service: IMessageService = Depends(get_message_service),
) -> IChatService:
    return ChatService(
        chat_repository=chat_repository,
        message_service=message_service,
    )


def get_project_service() -> IProjectService:
    return ProjectService()
