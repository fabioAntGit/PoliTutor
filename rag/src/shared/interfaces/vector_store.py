"""Vector store contract for retrieval and ingestion."""

from typing import Protocol, runtime_checkable

from ..models import RetrievalResults


@runtime_checkable
class IVectorStore(Protocol):
    def search(self, course: str, query_vector: list[float], top_k: int) -> RetrievalResults:
        """Return the top_k nearest chunks for query_vector, scoped to course."""
        ...

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        """Insert or update document embeddings and metadata, keyed by id."""
        ...

    def exists(self, filename: str) -> bool:
        """Return True if any chunk from this filename is already stored."""
        ...
