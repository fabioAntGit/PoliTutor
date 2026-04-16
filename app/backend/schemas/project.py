from pydantic import BaseModel

class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    institution: str
    configType: str
