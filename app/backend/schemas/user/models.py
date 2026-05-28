from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId

from app.backend.schemas.user.enums import UserRole

class User(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    email: str = Field(max_length=255)
    username: str = Field(max_length=255)
    role: UserRole
    hashed_password: str = Field(max_length=255)
    full_name: str = Field(max_length=255)
    courses: list[str] = Field(default_factory=list)
    must_change_password: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("id", mode="before")
    @classmethod
    def coerce_object_id(cls, v):
        if isinstance(v, ObjectId):
            return str(v)
        return v

    model_config = {"populate_by_name": True}
