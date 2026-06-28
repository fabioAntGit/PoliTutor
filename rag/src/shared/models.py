"""Shared RAG data models."""

from pydantic import BaseModel, Field

class RetrievalResults(BaseModel):
    """Aligned retrieval arrays from vector search and reranking."""
    ids: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)
    metadatas: list[dict[str, object]] = Field(default_factory=list)
    distances: list[float] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)

    @classmethod
    def from_chroma_dict(cls, results: dict[str, list]) -> "RetrievalResults":
        """Convert ChromaDB's first query result into RetrievalResults."""
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]

        scores = results.get("scores", [[]])[0]
        if not scores and distances:
            scores = [1.0 - d for d in distances]

        return cls(
            ids=list(ids) if ids else [],
            documents=list(results.get("documents", [[]])[0]),
            metadatas=list(results.get("metadatas", [[]])[0]),
            distances=list(distances) if distances else [],
            scores=list(scores) if scores else [],
        )

    def is_empty(self) -> bool:
        """Returns True if the result set contains no documents."""
        return len(self.ids) == 0

class TutorBenchmarkEntry(BaseModel):
    """One generated tutor-benchmark question."""
    filename: str
    page: str
    context: str
    question: str
    question_type: str
    expected_answer: str = ""

class TutorEvaluationResult(BaseModel):
    """Evaluation record for one tutor benchmark response."""
    filename: str
    page: str
    question: str
    question_type: str
    actual_response: str
    expected_answer: str
    faithfulness: int | None
    non_directiveness: int | None
    scaffolding: int | None
    clarity: int | None
    semantic_similarity: float | None
    is_fallback: bool
    is_guardrail: bool
    is_output_guardrail: bool
