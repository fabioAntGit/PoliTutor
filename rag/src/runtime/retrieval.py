"""Course-scoped retrieval and reranking."""

import logging

from ..shared.config import (
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    RERANKER_TOP_K,
    RETRIEVAL_DISTANCE_THRESHOLD,
    TOP_K_RESULTS,
)
from ..shared.embedding import get_embedder
from ..shared.interfaces.vector_store import IVectorStore
from ..shared.chroma_vector_store import ChromaVectorStore
from ..shared.models import RetrievalResults
from .reranker import rerank

logger = logging.getLogger(__name__)

def retrieve(
    course: str,
    query: str,
    *,
    embedding_model: str = EMBEDDING_MODEL,
    top_k: int = TOP_K_RESULTS,
    reranker_model: str | None = RERANKER_MODEL,
    reranker_top_k: int = RERANKER_TOP_K,
    collection_name: str = CHROMA_COLLECTION_NAME,
    distance_threshold: float | None = RETRIEVAL_DISTANCE_THRESHOLD,
    store: IVectorStore | None = None,
) -> RetrievalResults:
    """Retrieve course chunks, then apply distance filtering and reranking."""
    embedder = get_embedder(embedding_model)

    query_vector = embedder.embed_query(query)
    store = store or ChromaVectorStore(collection_name)
    results = store.search(course, query_vector, top_k=top_k)

    if distance_threshold is not None and not results.is_empty():
        mask = [d <= distance_threshold for d in results.distances]
        n_before = len(results.ids)
        results = RetrievalResults(
            ids=[v for v, m in zip(results.ids, mask) if m],
            documents=[v for v, m in zip(results.documents, mask) if m],
            metadatas=[v for v, m in zip(results.metadatas, mask) if m],
            distances=[v for v, m in zip(results.distances, mask) if m],
            scores=[v for v, m in zip(results.scores, mask) if m],
        )
        logger.info(
            "Distance threshold %.3f: %d/%d chunks kept",
            distance_threshold, len(results.ids), n_before,
        )

    if reranker_model:
        results = rerank(query, results, reranker_model, reranker_top_k)

    return results



