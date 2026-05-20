from pydantic import BaseModel, Field, ConfigDict

class ProjectRead(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: str
    institution: str
    config_type: str = Field(..., alias="configType")
    source: str | None = None


class ProjectDescriptionRead(BaseModel):
    project_id: str
    description: str
