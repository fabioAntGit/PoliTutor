from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from app.backend.schemas.shared.mongo import PyObjectId

class Chat(BaseModel):
    conversation_id: str = Field(
        default_factory=lambda: str(uuid4()),
        pattern=r"^[a-z0-9\-]+$",
        max_length=64,
    )
    project_id: str = Field(min_length=1, max_length=64)
    course: str = Field(min_length=1, max_length=64)
    user_id: str = Field(min_length=1, max_length=64)
    summary: Optional[str] = Field(default=None, max_length=1000)
    last_summarized_message_id: Optional[PyObjectId] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
