from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.backend.schemas.shared.mongo import PyObjectId

class Course(BaseModel):
    id: PyObjectId | None = Field(default=None, alias="_id")
    code: str = Field(max_length=64, description="Código único do curso, ex: 'ed'")
    name: str = Field(max_length=255, description="Nome completo do curso")
    scope: str = Field(description="Âmbito da cadeira")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
