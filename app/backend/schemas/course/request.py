from pydantic import BaseModel

class CourseCreateRequest(BaseModel):
    code: str
    name: str
    description: str = ""


class CourseUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
