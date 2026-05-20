from fastapi import APIRouter, Depends

from app.backend.schemas.project.response import ProjectRead, ProjectDescriptionRead
from app.backend.services.interfaces.project_service import IProjectService
from app.backend.api.deps import get_project_service

router = APIRouter()


@router.get("/projects", response_model=list[ProjectRead])
async def list_projects(service: IProjectService = Depends(get_project_service)):
    return await service.list_projects()


@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: str,
    service: IProjectService = Depends(get_project_service)
):
    return await service.get_project(project_id)


@router.get("/projects/{project_id}/description", response_model=ProjectDescriptionRead)
async def get_project_description(
    project_id: str,
    service: IProjectService = Depends(get_project_service)
):
    return await service.get_project_description(project_id)
