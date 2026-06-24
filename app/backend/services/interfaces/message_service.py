from typing import Protocol, runtime_checkable
from app.backend.schemas.message.models import Message
from contracts.rag.models import TutorResponse

@runtime_checkable
class IMessageService(Protocol):
    async def send_message(
        self,
        conversation_id: str,
        question: str,
        user_id: str,
    ) -> tuple[Message, Message, TutorResponse]:
        ...

    async def get_chat_messages(self, conversation_id: str) -> list[Message]:
        ...
