"""
Project Registry.

Maps frontend project IDs to RAG pipeline configuration.
To add a new project, add an entry here with the corresponding
course_code (used to filter ChromaDB metadata).
"""

from pydantic import BaseModel

class ProjectConfig(BaseModel):
    id: str
    name: str
    description: str
    institution: str
    config_type: str
    course_code: str

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
