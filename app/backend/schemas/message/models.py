from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class Role(str, Enum):
    user = "user"
    assistant = "assistant"

class Source(BaseModel):
    filename: str
    pages: list[int]

class Message(BaseModel):
    conversation_id: str = Field(pattern=r"^[a-z0-9\-]+$", max_length=64)
    role: Role
    content: str = Field(min_length=1, max_length=4000)
    sources: list[Source] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
