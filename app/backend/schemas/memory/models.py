from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MemoryType = Literal["difficulty", "preference", "goal", "progress"]


class UserMemory(BaseModel):
    id: str
    user_id: str
    course: str
    type: MemoryType
    topic: str
    content: str
    importance: float = Field(ge=0.0, le=10.0)
    last_seen_at: datetime
    created_at: datetime
