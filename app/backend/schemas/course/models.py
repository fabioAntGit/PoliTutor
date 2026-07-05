from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.backend.core.limits import COURSE_CODE_MAX_LENGTH, COURSE_NAME_MAX_LENGTH, COURSE_SCOPE_MAX_LENGTH
from app.backend.schemas.shared.mongo import PyObjectId

class Course(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    code: str = Field(max_length=COURSE_CODE_MAX_LENGTH, description="Código único do curso, ex: 'ed'")
    name: str = Field(max_length=COURSE_NAME_MAX_LENGTH, description="Nome completo do curso")
    scope: str = Field(max_length=COURSE_SCOPE_MAX_LENGTH, description="Âmbito da cadeira")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
