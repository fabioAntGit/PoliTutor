from typing import Protocol, runtime_checkable

from app.backend.schemas.chat.response import ChatRead, ChatCreated


@runtime_checkable
class IChatService(Protocol):
    async def create_chat(self, project_id: str, user_id: str) -> tuple[ChatCreated, bool]:
        ...

    async def get_chat(self, conversation_id: str, requester_user_id: str) -> ChatRead:
        ...
