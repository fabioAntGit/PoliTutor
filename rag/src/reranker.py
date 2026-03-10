"""
Reranking Service.
Reorders ChromaDB retrieval candidates using a cross-encoder model.
"""

import logging
from typing import Dict, Any

from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL, RERANKER_TOP_K

logger = logging.getLogger(__name__)

_reranker_cache: dict[str, CrossEncoder] = {}

def get_reranker_for_model(model_name: str) -> CrossEncoder:
    """Returns a cached cross-encoder for the given model name."""
    if model_name not in _reranker_cache:
        logger.info("Loading reranker model: %s", model_name)
        _reranker_cache[model_name] = CrossEncoder(model_name)
    return _reranker_cache[model_name]

def get_reranker() -> CrossEncoder:
    """Returns the default reranker defined in config."""
    return get_reranker_for_model(RERANKER_MODEL)

def rerank_with_model(
    query: str,
    results: Dict[str, Any],
    model_name: str,
    top_k: int,
) -> Dict[str, Any]:
    """
    Reranks ChromaDB candidates using the specified cross-encoder model.
    Returns the top `top_k` results sorted by cross-encoder score.
    """
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        logger.warning("Reranker received no documents to score.")
        return results

    reranker = get_reranker_for_model(model_name)
    pairs = [[query, doc] for doc in documents]
    scores = reranker.predict(pairs)

    candidates = sorted(
        zip(ids, documents, metadatas, distances, scores),
        key=lambda c: c[4],
        reverse=True,
    )

    top_candidates = candidates[:top_k]
    logger.info("Reranker '%s': %d candidates → top %d", model_name, len(ids), top_k)

    if not top_candidates:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]], "scores": [[]]}

    ids_r, docs_r, metas_r, dists_r, scores_r = zip(*top_candidates)
    return {
        "ids":       [list(ids_r)],
        "documents": [list(docs_r)],
        "metadatas": [list(metas_r)],
        "distances": [list(dists_r)],
        "scores":    [list(scores_r)],
    }

def rerank(query: str, results: Dict[str, Any]) -> Dict[str, Any]:
    """Reranks using the default model and top_k from config."""
    return rerank_with_model(query, results, RERANKER_MODEL, RERANKER_TOP_K)