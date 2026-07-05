from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.backend.schemas.shared.mongo import PyObjectId

class Chat(BaseModel):
    id: PyObjectId | None = Field(alias="_id", default=None)
    course_id: PyObjectId
    user_id: PyObjectId
    summary: str | None = Field(default=None, max_length=5000)
    last_summarized_message_id: PyObjectId | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
    }
