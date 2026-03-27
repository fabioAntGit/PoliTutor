"""
Project Registry.

Maps frontend project IDs to RAG pipeline configuration.
To add a new project, add an entry here with the corresponding
course_code (used to filter ChromaDB metadata) and collection_name.
"""

from dataclasses import dataclass

@dataclass
class ProjectConfig:
    course_code: str
    collection_name: str

PROJECT_REGISTRY: dict[str, ProjectConfig] = {
    "politutor": ProjectConfig(
        course_code="ed",
        collection_name="PoliTutor-Docs-bge-m3",
    ),
}