from pydantic import BaseModel, Field
from app.backend.schemas.message.models import Message

class ChatCreated(BaseModel):
    conversation_id: str

class ChatRead(BaseModel):
    conversation_id: str
    project_id: str
    project_name: str
    user_id: str
    summary: str | None = None
    messages: list[Message] = Field(default_factory=list)
