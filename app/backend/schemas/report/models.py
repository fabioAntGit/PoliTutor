from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.backend.schemas.shared.mongo import PyObjectId

class Report(BaseModel):
    conversation_id: str = Field(pattern=r"^[a-z0-9\-]+$", max_length=64)
    message_id: PyObjectId
    user_content: str = Field(min_length=1, max_length=1500)
    assistant_content: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
