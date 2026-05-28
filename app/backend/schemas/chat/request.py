from pydantic import BaseModel, Field

class ChatCreate(BaseModel):
    course_code: str = Field(min_length=1, max_length=64)
