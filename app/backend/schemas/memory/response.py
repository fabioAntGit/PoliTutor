from datetime import datetime

from pydantic import BaseModel

from app.backend.schemas.memory.models import MemoryType


class UserMemoryRead(BaseModel):
    id: str
    type: MemoryType
    content: str
    last_seen_at: datetime


class UserMemoryListRead(BaseModel):
    memories: list[UserMemoryRead]
