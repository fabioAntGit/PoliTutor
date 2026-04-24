from pydantic import BaseModel

from app.backend.schemas.shared.mongo import PyObjectId

class ReportCreate(BaseModel):
    message_id: PyObjectId
