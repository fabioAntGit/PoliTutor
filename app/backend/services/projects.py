from app.backend.core.projects import PROJECT_REGISTRY, get_project_detailed_description
from app.backend.schemas.project.response import ProjectRead, ProjectDescriptionRead
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
                config_type=config.config_type,
                source=config.source,
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
            config_type=project_config.config_type,
            source=project_config.source,
        )

    async def get_project_description(self, project_id: str) -> ProjectDescriptionRead:
        project_config = PROJECT_REGISTRY.get(project_id)
        if not project_config:
            raise ProjectNotFoundError(project_id)

        description = get_project_detailed_description(project_id)
        if not description:
            description = project_config.description

        return ProjectDescriptionRead(project_id=project_id, description=description)
