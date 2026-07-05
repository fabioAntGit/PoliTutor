from pydantic import BaseModel, Field

from app.backend.core.limits import COURSE_CODE_MAX_LENGTH, COURSE_NAME_MAX_LENGTH, COURSE_SCOPE_MAX_LENGTH

class CourseCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=COURSE_CODE_MAX_LENGTH)
    name: str = Field(min_length=1, max_length=COURSE_NAME_MAX_LENGTH)
    scope: str = Field(min_length=1, max_length=COURSE_SCOPE_MAX_LENGTH)


class CourseUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=COURSE_NAME_MAX_LENGTH)
    scope: str | None = Field(default=None, min_length=1, max_length=COURSE_SCOPE_MAX_LENGTH)
    is_active: bool | None = None
