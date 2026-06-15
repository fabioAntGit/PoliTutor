from typing import Protocol, runtime_checkable

from app.backend.schemas.chat.models import Chat
from app.backend.schemas.course.models import Course
from app.backend.schemas.message.models import Message


@runtime_checkable
class IChatService(Protocol):
    async def create_chat(self, course_code: str, user_id: str) -> str:
        ...

    async def get_chat(
        self, conversation_id: str, requester_user_id: str
    ) -> tuple[Chat, Course, list[Message]]:
        ...

    async def list_user_chats(self, user_id: str) -> list[tuple[Chat, Course]]:
        ...

    async def delete_chat(self, conversation_id: str, requester_user_id: str) -> None:
        ...
