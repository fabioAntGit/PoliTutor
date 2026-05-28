from pydantic import BaseModel
from app.backend.schemas.message.models import Source

class MessageResponse(BaseModel):
    user_message_id: str
    assistant_message_id: str
    answer: str
    sources: list[Source]
    is_fallback: bool
    guardrail_triggered: bool
