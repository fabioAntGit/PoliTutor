from datetime import datetime

from pydantic import BaseModel

from app.backend.schemas.memory.models import MemoryType


class UserMemoryRead(BaseModel):
    id: str
    type: MemoryType
    topic: str
    content: str
    importance: float
    last_seen_at: datetime
    created_at: datetime


class UserMemoryListRead(BaseModel):
    memories: list[UserMemoryRead]
    total: int


class MemoryUpdateRequest(BaseModel):
    content: str
