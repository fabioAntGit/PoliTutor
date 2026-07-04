"""Cross-encoder reranking for retrieved chunks."""

import logging
import torch.nn as nn

from sentence_transformers import CrossEncoder

from ..shared.config import RERANKER_MODEL, RERANKER_TOP_K, EMBEDDING_DEVICE
from ..shared.models import RetrievalResults

logger = logging.getLogger(__name__)

_reranker_cache: dict[str, CrossEncoder] = {}

def get_reranker(model_name: str | None = None) -> CrossEncoder:
    """Load or reuse a cached reranker."""
    model_name = model_name if model_name is not None else RERANKER_MODEL
    if not model_name:
        raise ValueError("RERANKER_MODEL is not configured.")

    if model_name not in _reranker_cache:
        logger.info("Loading reranker model: %s", model_name)
        _reranker_cache[model_name] = CrossEncoder(model_name, activation_fn=nn.Sigmoid(), trust_remote_code=True, device=EMBEDDING_DEVICE)
        
    return _reranker_cache[model_name]


def rerank(
    query: str,
    results: RetrievalResults,
    model_name: str | None = None,
    top_k: int | None = None,
) -> RetrievalResults:
    """Score candidates with a cross-encoder and return the top results."""
    if results.is_empty():
        logger.warning("Reranker received no documents to score.")
        return results

    model_name = model_name if model_name is not None else RERANKER_MODEL
    if not model_name:
        logger.info("Reranker disabled; returning vector search results.")
        return results

    top_k = top_k or RERANKER_TOP_K

    reranker = get_reranker(model_name)
    pairs = [[query, doc] for doc in results.documents]
    scores = reranker.predict(pairs)

    # Reranker score is the last tuple item.
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
