from pydantic import BaseModel

from app.backend.schemas.shared.mongo import PyObjectId
from app.backend.schemas.user.enums import UserRole

class UserCreateRequest(BaseModel):
    email: str
    password: str
    full_name: str
    role: UserRole
    courses: list[PyObjectId]

class UserUpdateRequest(BaseModel):
    email: str | None = None
    full_name: str | None = None
    role: UserRole | None = None
    courses: list[PyObjectId] | None = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
