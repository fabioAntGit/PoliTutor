"""
Reranking Service.
Reorders ChromaDB retrieval candidates using a cross-encoder model.
"""

import logging
from typing import Dict, Any

from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL, RERANKER_TOP_K

logger = logging.getLogger(__name__)

_reranker: CrossEncoder | None = None

def get_reranker() -> CrossEncoder:
    """Returns a singleton instance of the cross-encoder model."""
    global _reranker
    
    if _reranker is None:
        logger.info("Loading reranker model: %s", RERANKER_MODEL)
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker

def rerank(query: str, results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reranks ChromaDB candidates using a cross-encoder and returns the top RERANKER_TOP_K.

    The cross-encoder receives (query, document) pairs and assigns a relevance
    score to each. Results are sorted by this score in descending order.
    """
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        logger.warning("Reranker received no documents to score.")
        return results

    reranker = get_reranker()

    pairs = [[query, doc] for doc in documents]
    scores = reranker.predict(pairs)

    candidates = sorted(
        zip(ids, documents, metadatas, distances, scores),
        key=lambda candidate: candidate[4],
        reverse=True,
    )

    top_candidates = candidates[:RERANKER_TOP_K]
    logger.info("Reranker: %d candidates → top %d", len(ids), RERANKER_TOP_K)

    if not top_candidates:
        return {
            "ids": [[]], "documents": [[]], "metadatas": [[]],
            "distances": [[]], "scores": [[]]
        }

    ids_r, docs_r, metas_r, dists_r, scores_r = zip(*top_candidates)

    return {
        "ids":       [list(ids_r)],
        "documents": [list(docs_r)],
        "metadatas": [list(metas_r)],
        "distances": [list(dists_r)],
        "scores":    [list(scores_r)],
    }