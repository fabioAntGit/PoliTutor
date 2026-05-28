from typing import Protocol, runtime_checkable

from app.backend.schemas.chat.response import ChatRead, ChatCreated, ChatListItem


@runtime_checkable
class IChatService(Protocol):
    async def create_chat(self, course_code: str, user_id: str) -> ChatCreated:
        ...

    async def get_chat(self, conversation_id: str, requester_user_id: str) -> ChatRead:
        ...

    async def list_user_chats(self, user_id: str) -> list[ChatListItem]:
        ...
