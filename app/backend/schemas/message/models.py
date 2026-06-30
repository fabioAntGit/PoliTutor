from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.backend.schemas.shared.mongo import PyObjectId
from app.backend.schemas.message.enums import Role

class Source(BaseModel):
    filename: str
    pages: list[int]

class Message(BaseModel):
    id: PyObjectId | None = Field(alias="_id", default=None)
    conversation_id: PyObjectId
    role: Role
    content: str = Field(min_length=1)
    sources: list[Source] = Field(default_factory=list)
    is_reported: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
    }
