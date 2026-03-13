"""
Reranking Service.

This module provides functions to load, cache, and apply cross-encoder AI models 
to a set of pre-fetched ChromaDB candidate documents. It assigns a new semantic 
relevance score to each chunk based on the exact query and reorders them.
"""

import logging
import torch.nn as nn

from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL, RERANKER_TOP_K
from models import RetrievalResults

logger = logging.getLogger(__name__)

_reranker_cache: dict[str, CrossEncoder] = {}

def get_reranker(model_name: str | None = None) -> CrossEncoder:
    """
    Returns a cached cross-encoder model, loading it on first use.

    Args:
        model_name: HuggingFace model identifier. Uses config default if None.

    Returns:
        The loaded CrossEncoder instance ready for pair scoring.
    """
    model_name = model_name or RERANKER_MODEL

    if model_name not in _reranker_cache:
        logger.info("Loading reranker model: %s", model_name)
        _reranker_cache[model_name] = CrossEncoder(model_name, activation_fn=nn.Sigmoid(), trust_remote_code=True)
        
    return _reranker_cache[model_name]

def rerank(
    query: str,
    results: RetrievalResults,
    model_name: str | None = None,
    top_k: int | None = None,
) -> RetrievalResults:
    """
    Applies a Cross-Encoder model to score and reorder an initial set of candidates.

    The original ChromaDB vector distances are preserved; the cross-encoder adds a
    new semantic similarity score to each chunk and reorders them by that score.
    Only the top_k highest-scoring chunks are returned.

    Args:
        query: The user's specific context or question.
        results: The chunks initially retrieved from ChromaDB.
        model_name: Reranker model identifier to use. Uses config default if None.
        top_k: Maximum number of candidates to return after scoring. Uses config default if None.

    Returns:
        A new RetrievalResults sorted by cross-encoder score, containing only the top_k chunks.
    """
    if results.is_empty():
        logger.warning("Reranker received no documents to score.")
        return results

    model_name = model_name or RERANKER_MODEL
    top_k = top_k or RERANKER_TOP_K

    reranker = get_reranker(model_name)
    pairs = [[query, doc] for doc in results.documents]
    scores = reranker.predict(pairs)

    # Tuple layout: (id, document, metadata, distance, score) — index 4 is the reranker score
    candidates = sorted(
        zip(results.ids, results.documents, results.metadatas, results.distances, scores),
        key=lambda c: c[4],
        reverse=True,
    )

    top_candidates = candidates[:top_k]
    logger.info("Reranker '%s': %d candidates → top %d", model_name, len(results.ids), top_k)

    if not top_candidates:
        return RetrievalResults()

    ids_r, docs_r, metas_r, dists_r, scores_r = zip(*top_candidates)
    return RetrievalResults(
        ids=list(ids_r),
        documents=list(docs_r),
        metadatas=list(metas_r),
        distances=list(dists_r),
        scores=list(scores_r),
    )