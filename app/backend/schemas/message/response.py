from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.backend.schemas.message.enums import Role
from contracts.rag.models import TutorSource


class MessageRead(BaseModel):
    id: str
    role: Role
    content: str
    sources: list[TutorSource] = Field(default_factory=list)
    is_reported: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    user_message_id: str
    assistant_message_id: str
    answer: str
    sources: list[TutorSource]
    is_fallback: bool
