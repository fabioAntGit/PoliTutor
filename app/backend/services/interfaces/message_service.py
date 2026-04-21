from typing import Protocol, runtime_checkable
from app.backend.schemas.message.response import MessageResponse
from app.backend.schemas.message.models import Message

@runtime_checkable
class IMessageService(Protocol):
    async def send_message(
        self, 
        conversation_id: str,
        question: str,
        iaedu_endpoint: str,
        iaedu_api_key: str,
        iaedu_channel_id: str
    ) -> MessageResponse:
        ...

    async def get_chat_messages(self, conversation_id: str) -> list[Message]:
        ...

    async def get_or_load_context(self, conversation_id: str) -> tuple[str | None, list[Message]]:
        ...
