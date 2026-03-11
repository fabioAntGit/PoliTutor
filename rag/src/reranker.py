"""
Reranking Service.

This module provides functions to load, cache, and apply cross-encoder AI models 
to a set of pre-fetched ChromaDB candidate documents. It assigns a new semantic 
relevance score to each chunk based on the exact query and reorders them.
"""

import logging

from sentence_transformers import CrossEncoder

from config import RERANKER_MODEL, RERANKER_TOP_K
from models import RetrievalResults

logger = logging.getLogger(__name__)

_reranker_cache: dict[str, CrossEncoder] = {}

def get_reranker(model_name: str | None = None) -> CrossEncoder:
    """
    Retrieves or initializes a cross-encoder language model.
    Models are cached in memory to avoid the massive performance penalty of reloading 
    HuggingFace models on every RAG query.

    Args:
        model_name (str | None): The HuggingFace model identifier. Defaults to config if None.

    Returns:
        CrossEncoder: The loaded model instance ready for pair scoring.
    """
    model_name = model_name or RERANKER_MODEL

    if model_name not in _reranker_cache:
        logger.info("Loading reranker model: %s", model_name)
        _reranker_cache[model_name] = CrossEncoder(model_name)
        
    return _reranker_cache[model_name]

def rerank(
    query: str,
    results: RetrievalResults,
    model_name: str | None = None,
    top_k: int | None = None,
) -> RetrievalResults:
    """
    Receives an initial set of RetrievalResults and applies the Cross-Encoder model
    to generate highly accurate semantic similarity scores, overwriting the old 
    vector-based distances and reordering the documents.

    Args:
        query (str): The user's specific context or question.
        results (RetrievalResults): The chunks initially retrieved from ChromaDB.
        model_name (str | None): Reranker model identifier to use.
        top_k (int | None): Maximum number of candidates to return after scoring.

    Returns:
        RetrievalResults: A new sorted object containing only the top_k most relevant chunks.
    """
    if results.is_empty():
        logger.warning("Reranker received no documents to score.")
        return results

    model_name = model_name or RERANKER_MODEL
    top_k = top_k or RERANKER_TOP_K

    reranker = get_reranker(model_name)
    pairs = [[query, doc] for doc in results.documents]
    scores = reranker.predict(pairs)

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