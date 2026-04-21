from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class Role(str, Enum):
    user = "user"
    assistant = "assistant"

class Source(BaseModel):
    filename: str
    pages: list[int]

from typing import Optional, Any
from pydantic import BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(lambda v: str(v) if v else None)]

class Message(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    conversation_id: str = Field(pattern=r"^[a-z0-9\-]+$", max_length=64)
    role: Role
    content: str = Field(min_length=1, max_length=4000)
    sources: list[Source] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
    }
