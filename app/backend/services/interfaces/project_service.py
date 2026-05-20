from typing import Protocol, runtime_checkable
from app.backend.schemas.project.response import ProjectRead, ProjectDescriptionRead

@runtime_checkable
class IProjectService(Protocol):
    async def list_projects(self) -> list[ProjectRead]:
        ...

    async def get_project(self, project_id: str) -> ProjectRead:
        ...

    async def get_project_description(self, project_id: str) -> ProjectDescriptionRead:
        ...
