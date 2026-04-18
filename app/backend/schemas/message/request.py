from pydantic import BaseModel, Field
from app.backend.core.config import QUERY_MAX_LENGTH


class MessageSend(BaseModel):
    question: str = Field(min_length=1, max_length=QUERY_MAX_LENGTH)


class MessageCredentials(BaseModel):
    x_iaedu_api_key: str = Field(
        alias="X-IAEdu-API-Key",
        pattern=r"^sk-usr-",
        max_length=128
    )
    x_iaedu_endpoint: str = Field(
        alias="X-IAEdu-Endpoint",
        pattern=r"^https://api\.iaedu\.pt/agent-chat//api/v1/agent/",
        max_length=256
    )
    x_iaedu_channel_id: str = Field(
        alias="X-IAEdu-Channel-ID",
        pattern=r"^[a-z0-9]+$",
        max_length=64
    )
