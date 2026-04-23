from pydantic import BaseModel, Field
from app.backend.core.config import QUERY_MAX_LENGTH


class MessageSend(BaseModel):
    question: str = Field(min_length=1, max_length=QUERY_MAX_LENGTH)
