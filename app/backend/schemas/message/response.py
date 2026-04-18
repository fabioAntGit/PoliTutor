from pydantic import BaseModel
from app.backend.schemas.message.models import Source

class MessageResponse(BaseModel):
    answer: str
    sources: list[Source]
    is_fallback: bool
    guardrail_triggered: bool
