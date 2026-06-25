from app.backend.core.exceptions import (
    ChatNotFoundError,
    CourseNotFoundError,
    AccessDeniedError,
    UserNotFoundError,
)
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.repositories.interfaces.report_repository import IReportRepository
from app.backend.schemas.chat.models import Chat
from app.backend.schemas.course.models import Course
from app.backend.schemas.message.models import Message
from app.backend.services.interfaces.chat_service import IChatService


class ChatService(IChatService):
    def __init__(
        self,
        chat_repository: IChatRepository,
        course_repository: ICourseRepository,
        user_repository: IUserRepository,
        message_repository: IMessageRepository,
        report_repository: IReportRepository,
    ) -> None:
        self.chat_repository = chat_repository
        self.course_repository = course_repository
        self.user_repository = user_repository
        self.message_repository = message_repository
        self.report_repository = report_repository

    async def create_chat(self, course_code: str, user_id: str) -> str:
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

        return await self.chat_repository.create(chat)

    async def get_chat(
        self, conversation_id: str, requester_user_id: str
    ) -> tuple[Chat, Course, list[Message]]:
        chat = await self.chat_repository.get_chat(conversation_id)

        if chat is None:
            raise ChatNotFoundError(conversation_id)

        if chat.user_id != requester_user_id:
            raise AccessDeniedError("Nao tens permissao para aceder a este chat.")

        course = await self.course_repository.find_by_code(chat.course)

        if course is None or not course.is_active:
            raise CourseNotFoundError(chat.course)

        messages = await self.message_repository.get_messages(conversation_id)

        return chat, course, messages

    async def delete_chat(self, conversation_id: str, requester_user_id: str) -> None:
        chat = await self.chat_repository.get_chat(conversation_id)

        if chat is None:
            raise ChatNotFoundError(conversation_id)

        if chat.user_id != requester_user_id:
            raise AccessDeniedError("Nao tens permissao para eliminar este chat.")

        await self.report_repository.delete_by_conversation(conversation_id)
        await self.message_repository.delete_by_conversation(conversation_id)
        await self.chat_repository.delete(conversation_id)

    async def list_user_chats(self, user_id: str) -> list[tuple[Chat, Course]]:
        chats = await self.chat_repository.get_chats(user_id)

        course_codes = list({chat.course for chat in chats})
        courses = await self.course_repository.get_courses_by_codes(course_codes)
        active_by_code = {course.code: course for course in courses if course.is_active}

        items = [
            (chat, active_by_code[chat.course])
            for chat in chats
            if chat.course in active_by_code
        ]

        items.sort(key=lambda item: item[0].updated_at, reverse=True)
        return items
