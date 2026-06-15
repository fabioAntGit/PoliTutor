from pydantic import BaseModel, Field
from app.backend.core.config import QUERY_MAX_LENGTH, QUERY_MIN_LENGTH


class MessageSend(BaseModel):
    question: str = Field(min_length=QUERY_MIN_LENGTH, max_length=QUERY_MAX_LENGTH)
