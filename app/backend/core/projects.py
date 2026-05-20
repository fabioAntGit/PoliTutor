"""
Project Registry.

Maps frontend project IDs to RAG pipeline configuration.
To add a new project, add an entry here with the corresponding
course_code (used to filter ChromaDB metadata).
"""

import json
import logging
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)

_DYNAMIC_PROJECTS_BASE_DIR = Path(__file__).resolve().parents[3] / "DynamicGr" / "projects"
_DYNAMIC_CONTEXT_DIR = _DYNAMIC_PROJECTS_BASE_DIR / "projects_context"
_DYNAMIC_DESCRIPTIONS_DIR = _DYNAMIC_PROJECTS_BASE_DIR / "projects_descriptions"


class ProjectConfig(BaseModel):
    id: str
    name: str
    description: str
    institution: str
    config_type: str
    course_code: str
    source: str | None = None


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.warning("Failed to read project context: %s", path)
        return {}


def _extract_context_description(data: dict) -> str:
    org_profile = (
        data.get("final_result", {})
        .get("enterpriseTopicContext", {})
        .get("org_profile", {})
    )

    return str(
        org_profile.get("public_description")
        or org_profile.get("description")
        or ""
    )


def get_project_detailed_description(project_id: str) -> str:
    description_file = _DYNAMIC_DESCRIPTIONS_DIR / f"{project_id}.json"
    if not description_file.exists():
        return ""

    desc_data = _read_json(description_file)
    return str(desc_data.get("description") or "")


def _load_dynamic_projects() -> dict[str, ProjectConfig]:
    context_dir = _DYNAMIC_CONTEXT_DIR

    if not context_dir.exists():
        logger.warning("DynamicGr context dir not found: %s", context_dir)
        return {}

    logger.info("Loading DynamicGr projects from: %s", context_dir)

    projects: dict[str, ProjectConfig] = {}
    for context_file in context_dir.glob("*.json"):
        logger.info("Loading DynamicGr context file: %s", context_file.name)
        data = _read_json(context_file)
        org_profile = (
            data.get("final_result", {})
            .get("enterpriseTopicContext", {})
            .get("org_profile", {})
        )

        project_id = context_file.stem
        org_name = str(org_profile.get("name") or project_id)
        description = _extract_context_description(data)

        projects[project_id] = ProjectConfig(
            id=project_id,
            name=org_name,
            description=description,
            institution=org_name,
            config_type="iaedu",
            course_code=project_id,
            source="Dynamic",
        )

    logger.info("Loaded DynamicGr projects: %s", list(projects.keys()))

    return projects


PROJECT_REGISTRY: dict[str, ProjectConfig] = {
    "politutor": ProjectConfig(
        id="politutor",
        name="Poli Tutor",
        description="Tutor socrático baseado em RAG que guia o estudante através de perguntas e pistas, sem nunca dar respostas diretas. Atualmente com conhecimento sobre a UC de Estruturas de Dados (ESTG/IPP) — listas, árvores, grafos, algoritmos de ordenação e pesquisa.",
        institution="ESTG — Instituto Politécnico do Porto",
        config_type="iaedu",
        course_code="ed",
    ),
}

PROJECT_REGISTRY.update(_load_dynamic_projects())
