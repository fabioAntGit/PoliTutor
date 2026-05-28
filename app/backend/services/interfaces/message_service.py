from typing import Protocol, runtime_checkable
from app.backend.schemas.message.response import MessageResponse
from app.backend.schemas.message.models import Message

@runtime_checkable
class IMessageService(Protocol):
    async def send_message(
        self, 
        conversation_id: str,
        question: str,
        user_id: str,
    ) -> MessageResponse:
        ...

    async def get_chat_messages(self, conversation_id: str) -> list[Message]:
        ...
