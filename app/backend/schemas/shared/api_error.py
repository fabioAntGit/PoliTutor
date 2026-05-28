from typing import Any

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    code: str = Field(pattern=r"^[a-z0-9_]+$", max_length=64)
    message: str = Field(min_length=1, max_length=255)
    details: dict[str, Any] | None = None
