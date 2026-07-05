from pydantic import BaseModel, Field

from app.backend.core.limits import PASSWORD_MIN_LENGTH, USER_TEXT_MAX_LENGTH
from app.backend.schemas.shared.mongo import PyObjectId
from app.backend.schemas.user.enums import UserRole

class UserCreateRequest(BaseModel):
    email: str = Field(min_length=1, max_length=USER_TEXT_MAX_LENGTH)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH)
    full_name: str = Field(min_length=1, max_length=USER_TEXT_MAX_LENGTH)
    role: UserRole
    courses: list[PyObjectId]

class UserUpdateRequest(BaseModel):
    email: str | None = Field(default=None, min_length=1, max_length=USER_TEXT_MAX_LENGTH)
    full_name: str | None = Field(default=None, min_length=1, max_length=USER_TEXT_MAX_LENGTH)
    role: UserRole | None = None
    courses: list[PyObjectId] | None = None

class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH)
