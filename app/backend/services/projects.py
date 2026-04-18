from app.backend.repositories.projects import PROJECT_REGISTRY
from app.backend.schemas.project.response import ProjectRead
from app.backend.core.exceptions import ProjectNotFoundError
from app.backend.services.interfaces.project_service import IProjectService

class ProjectService(IProjectService):
    async def list_projects(self) -> list[ProjectRead]:
        return [
            ProjectRead(
                id=config.id,
                name=config.name,
                description=config.description,
                institution=config.institution,
                configType=config.configType,
            )
            for config in PROJECT_REGISTRY.values()
        ]

    async def get_project(self, project_id: str) -> ProjectRead:
        project_config = PROJECT_REGISTRY.get(project_id)
        if not project_config:
            raise ProjectNotFoundError(project_id)

        return ProjectRead(
            id=project_config.id,
            name=project_config.name,
            description=project_config.description,
            institution=project_config.institution,
            configType=project_config.configType,
        )
