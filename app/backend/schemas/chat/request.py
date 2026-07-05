from pydantic import BaseModel

from app.backend.schemas.shared.mongo import PyObjectId

class ChatCreate(BaseModel):
    course_id: PyObjectId
