from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.backend.schemas.shared.mongo import PyObjectId

class Role(str, Enum):
    user = "user"
    assistant = "assistant"

class Source(BaseModel):
    filename: str
    pages: list[int]

class Message(BaseModel):
    id: PyObjectId | None = Field(alias="_id", default=None)
    conversation_id: str = Field(pattern=r"^[a-z0-9\-]+$", max_length=64)
    role: Role
    content: str = Field(min_length=1)
    sources: list[Source] = Field(default_factory=list)
    is_reported: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
    }
