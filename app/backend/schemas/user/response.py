from pydantic import BaseModel

from app.backend.schemas.user.enums import UserRole

class UserResponse(BaseModel):
    username: str
    email: str
    full_name: str
    role: UserRole
    courses: list[str]
    must_change_password: bool = False
