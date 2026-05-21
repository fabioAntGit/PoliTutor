from pydantic import BaseModel

class CourseCreateRequest(BaseModel):
    code: str
    name: str
    description: str = ""
