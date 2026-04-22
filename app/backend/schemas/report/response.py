from pydantic import BaseModel

class ReportResponse(BaseModel):
    success: bool
