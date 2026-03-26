"""
Shared Data Models.

Defines the core data structures used to pass information safely and
consistently between different components of the RAG pipeline.

Classes:
    RetrievalResults: Output of ChromaDB query + reranking stage.
    TutorSource:      A single source chunk cited in a tutor response.
    TutorResponse:    Final output of the tutor generation pipeline.
"""

from dataclasses import dataclass, field

@dataclass
class RetrievalResults:
    """
    Encapsulates the results from a ChromaDB query and subsequent RAG operations.
    Provides a structured, type-safe alternative to nested dictionary unpacking.
    """
    ids: list[str] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    metadatas: list[dict[str, object]] = field(default_factory=list)
    distances: list[float] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)

    @classmethod
    def from_chroma_dict(cls, results: dict[str, list]) -> "RetrievalResults":
        """
        Converts the raw ChromaDB output dictionary into a RetrievalResults instance.

        If scores are absent, derives them from cosine distances via `1.0 - distance`.

        Args:
            results: Raw ChromaDB query output with nested lists under 'ids',
                     'documents', 'metadatas', 'distances', and optionally 'scores'.

        Returns:
            A populated RetrievalResults instance.
        """
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


@dataclass
class TutorSource:
    """
    Represents a single source chunk cited in a tutor response.

    Attributes:
        filename: Name of the source document (e.g. 'slides.ED.CAP3.pdf').
        pages:    List of page numbers covered by this chunk.
        score:    Reranker relevance score in [0, 1].
    """
    filename: str
    pages: list[int]

@dataclass
class TutorResponse:
    """
    Final output of the tutor generation pipeline.

    Attributes:
        answer:      The tutor's response text (Socratic guidance or fallback message).
        sources:     List of source chunks used to ground the response.
        is_fallback: True if no relevant context was found and a fallback message was returned.
    """
    answer: str
    sources: list[TutorSource]
    is_fallback: bool