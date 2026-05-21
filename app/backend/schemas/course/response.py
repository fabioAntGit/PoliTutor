from pydantic import BaseModel

class CourseResponse(BaseModel):
    code: str
    name: str
    description: str
