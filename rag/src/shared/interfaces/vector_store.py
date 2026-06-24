from typing import Protocol, runtime_checkable

from ..models import RetrievalResults


@runtime_checkable
class IVectorStore(Protocol):
    """Port consumed by the RAG to talk to a vector database."""

    def search(self, course: str, query_vector: list[float], top_k: int) -> RetrievalResults:
        """Similarity search for a course, returning domain results."""
        ...

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        """Insert or update embedded documents."""
        ...

    def exists(self, filename: str) -> bool:
        """Whether any chunk for the given filename is already stored."""
        ...
