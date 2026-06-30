from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.backend.schemas.shared.mongo import PyObjectId

MemoryType = Literal["difficulty", "preference", "goal", "progress"]


class UserMemory(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    user_id: PyObjectId
    course_id: PyObjectId
    type: MemoryType
    topic: str
    content: str
    importance: float = Field(ge=0.0, le=10.0)
    last_seen_at: datetime
    created_at: datetime

    model_config = {"populate_by_name": True}
