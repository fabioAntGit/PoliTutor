from typing import List
from fastapi import APIRouter, HTTPException
from app.backend.repositories.projects import PROJECT_REGISTRY
from app.backend.schemas.project import ProjectOut

router = APIRouter()

@router.get("/projects", response_model=List[ProjectOut])
def get_projects():
    projects = []
    for project_id, project_config in PROJECT_REGISTRY.items():
        projects.append(
            ProjectOut(
                id=project_config.id,
                name=project_config.name,
                description=project_config.description,
                institution=project_config.institution,
                configType=project_config.configType,
            )
        )
    return projects

@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: str):
    project_config = PROJECT_REGISTRY.get(project_id)
    if not project_config:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    return ProjectOut(
        id=project_config.id,
        name=project_config.name,
        description=project_config.description,
        institution=project_config.institution,
        configType=project_config.configType,
    )
