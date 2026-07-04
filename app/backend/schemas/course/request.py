from pydantic import BaseModel, Field

class CourseCreateRequest(BaseModel):
    code: str
    name: str
    scope: str = Field(min_length=1)


class CourseUpdateRequest(BaseModel):
    name: str | None = None
    scope: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None
