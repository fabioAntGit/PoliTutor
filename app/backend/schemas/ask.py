"""
Pydantic schemas for the /ask endpoint.
"""

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from app.backend.core.config import QUERY_MAX_LENGTH


class AskRequest(BaseModel):
    conversation_id: str = Field(pattern=r"^[a-z0-9\-]+$", max_length=64)
    question: str = Field(min_length=1, max_length=QUERY_MAX_LENGTH)
    iaedu_endpoint: AnyHttpUrl
    iaedu_api_key: str = Field(pattern=r"^sk-usr-[a-z0-9]+$", max_length=128)
    iaedu_channel_id: str = Field(pattern=r"^[a-z0-9]+$", max_length=64)

    @field_validator("iaedu_api_key", "iaedu_channel_id", mode="before")
    @classmethod
    def strip_credentials(cls, v: str) -> str:
        return v.strip()


class SourceOut(BaseModel):
    filename: str
    pages: list[int]


class AskResponseOut(BaseModel):
    answer: str
    sources: list[SourceOut]
    is_fallback: bool
    guardrail_triggered: bool
