from app.backend.core.exceptions import (
    ChatNotFoundError,
    CourseNotFoundError,
    AccessDeniedError,
    UserNotFoundError,
)
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.schemas.chat.models import Chat
from app.backend.schemas.chat.response import ChatRead, ChatCreated, ChatListItem
from app.backend.services.interfaces.chat_service import IChatService
from app.backend.services.interfaces.message_service import IMessageService


class ChatService(IChatService):
    def __init__(
        self,
        chat_repository: IChatRepository,
        course_repository: ICourseRepository,
        user_repository: IUserRepository,
        message_service: IMessageService,
    ) -> None:
        self.chat_repository = chat_repository
        self.course_repository = course_repository
        self.user_repository = user_repository
        self.message_service = message_service

    async def create_chat(self, course_code: str, user_id: str) -> ChatCreated:
        course = await self.course_repository.find_by_code(course_code)

        if course is None or not course.is_active:
            raise CourseNotFoundError(course_code)

        user = await self.user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError()

        if course.code not in user.courses:
            raise AccessDeniedError(
                message="Não tens permissão para criar conversas nesta cadeira."
            )

        chat = Chat(
            course=course.code,
            user_id=user_id,
        )

        conversation_id = await self.chat_repository.create(chat)
        return ChatCreated(conversation_id=conversation_id)

    async def get_chat(self, conversation_id: str, requester_user_id: str) -> ChatRead:
        chat = await self.chat_repository.get_chat(conversation_id)

        if chat is None:
            raise ChatNotFoundError(conversation_id)

        if chat.user_id != requester_user_id:
            raise AccessDeniedError("Nao tens permissao para aceder a este chat.")

        course = await self.course_repository.find_by_code(chat.course)

        if course is None or not course.is_active:
            raise CourseNotFoundError(chat.course)

        messages = await self.message_service.get_chat_messages(conversation_id)

        return ChatRead(
            conversation_id=str(chat.id),
            course_code=course.code,
            course_name=course.name,
            user_id=chat.user_id,
            summary=chat.summary,
            messages=messages,
        )

    async def list_user_chats(self, user_id: str) -> list[ChatListItem]:
        chats = await self.chat_repository.get_chats(user_id)

        course_codes = list({chat.course for chat in chats})
        courses = await self.course_repository.get_courses_by_codes(course_codes)
        active_by_code = {course.code: course for course in courses if course.is_active}

        items = [
            ChatListItem(
                conversation_id=str(chat.id),
                course_name=active_by_code[chat.course].name,
                updated_at=chat.updated_at,
            )
            for chat in chats
            if chat.course in active_by_code
        ]

        items.sort(key=lambda item: item.updated_at, reverse=True)
        return items
