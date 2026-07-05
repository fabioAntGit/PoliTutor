from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.backend.schemas.shared.mongo import PyObjectId

MemoryType = Literal["difficulty", "preference", "goal", "progress"]


class ExtractedMemory(BaseModel):
    """One memory extracted by the LLM from a conversation summary."""

    type: MemoryType
    topic: str
    content: str
    importance: float

    @field_validator("importance")
    @classmethod
    def _clamp_importance(cls, v: float) -> float:
        return max(0.0, min(10.0, v))


class MemoryExtraction(BaseModel):
    """Structured LLM reply for memory extraction (MEMORY_EXTRACTION_PROMPT)."""

    memories: list[ExtractedMemory] = []


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
