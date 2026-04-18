from pydantic import BaseModel

class ChatCreate(BaseModel):
    project_id: str
    user_id: str
