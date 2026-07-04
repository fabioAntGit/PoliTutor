from pydantic import BaseModel

class CourseResponse(BaseModel):
    id: str
    code: str
    name: str
    scope: str
    is_active: bool = True
