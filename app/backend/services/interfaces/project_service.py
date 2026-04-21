from typing import Protocol, runtime_checkable
from app.backend.schemas.project.response import ProjectRead

@runtime_checkable
class IProjectService(Protocol):
    async def list_projects(self) -> list[ProjectRead]:
        ...

    async def get_project(self, project_id: str) -> ProjectRead:
        ...
