from datetime import datetime
from pydantic import BaseModel, Field
from app.backend.schemas.message.response import MessageRead

class ChatCreated(BaseModel):
    conversation_id: str

class ChatRead(BaseModel):
    course_name: str
    messages: list[MessageRead] = Field(default_factory=list)

class ChatListItem(BaseModel):
    conversation_id: str
    course_name: str
    updated_at: datetime
