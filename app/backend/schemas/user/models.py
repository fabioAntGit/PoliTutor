from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.backend.core.limits import USER_TEXT_MAX_LENGTH
from app.backend.schemas.shared.mongo import PyObjectId
from app.backend.schemas.user.enums import UserRole

class User(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    email: str = Field(max_length=USER_TEXT_MAX_LENGTH)
    username: str = Field(max_length=USER_TEXT_MAX_LENGTH)
    role: UserRole
    hashed_password: str = Field(max_length=USER_TEXT_MAX_LENGTH)
    full_name: str = Field(max_length=USER_TEXT_MAX_LENGTH)
    courses: list[PyObjectId] = Field(default_factory=list)
    must_change_password: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
