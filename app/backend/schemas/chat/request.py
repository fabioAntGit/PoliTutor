from pydantic import BaseModel, Field

class ChatCreate(BaseModel):
    project_id: str = Field(min_length=1, max_length=64)
