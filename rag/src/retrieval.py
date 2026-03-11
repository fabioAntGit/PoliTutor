"""
Retrieval Module.

This is the primary search execution component of the RAG system. It exposes
functions to fetch, rerank, threshold, and display information chunks corresponding
to the user's queries against the ChromaDB document store.
"""

import logging

from config import TOP_K_RESULTS, EMBEDDING_MODEL, CHROMA_COLLECTION_NAME, RERANKER_MODEL, RERANKER_TOP_K, RERANKER_SCORE_THRESHOLD
from embedding import get_embedder
from database import get_collection
from models import RetrievalResults
from reranker import rerank

logger = logging.getLogger(__name__)

def apply_threshold(results: RetrievalResults, threshold: float) -> RetrievalResults:
    """
    Filters out any retrieved chunks whose relevance score strictly falls below 
    the provided confidence threshold. Keeps the high-quality signals and removes noise.

    Args:
        results (RetrievalResults): The scored chunk candidates.
        threshold (float): Minimum acceptable score.

    Returns:
        RetrievalResults: A subset containing only candidates satisfying (score >= threshold).
    """
    if results.is_empty():
        return results

    kept = [(i, d, m, dist, s) for i, d, m, dist, s in
            zip(results.ids, results.documents, results.metadatas, results.distances, results.scores) if s >= threshold]

    if not kept:
        return RetrievalResults()

    ids_f, docs_f, metas_f, dists_f, scores_f = zip(*kept)
    return RetrievalResults(
        ids=list(ids_f),
        documents=list(docs_f),
        metadatas=list(metas_f),
        distances=list(dists_f),
        scores=list(scores_f),
    )


def retrieve_with_config(
    course: str,
    query: str,
    *,
    embedding_model: str = EMBEDDING_MODEL,
    collection_name: str = CHROMA_COLLECTION_NAME,
    top_k: int = TOP_K_RESULTS,
    reranker_model: str | None = RERANKER_MODEL,
    reranker_top_k: int = RERANKER_TOP_K,
    score_threshold: float | None = None,
) -> Dict[str, Any]:
    """
    Flexible retrieval for benchmarking. Supports custom embedding models,
    ChromaDB collections, rerankers, and score thresholds.

    Args:
        course:           Course unit identifier (e.g. 'ed').
        query:            The user's question.
        embedding_model:  HuggingFace model name to embed the query.
        collection_name:  ChromaDB collection to query.
        top_k:            Number of initial candidates to retrieve.
        reranker_model:   Cross-encoder model name, or None to skip reranking.
        reranker_top_k:   Number of results to keep after reranking.
        score_threshold:  Minimum score to keep a result (applied after reranking).

    Returns:
        Structured RetrievalResults with aligned arrays of ids, documents, metadatas, distances, scores.
    """
    collection = get_collection(collection_name)
    embedder   = get_embedder(embedding_model)

    query_vector = embedder.embed_query(query)

    raw = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        where={"course": course.strip().lower()},
    )

    results = RetrievalResults.from_chroma_dict(raw)

    if reranker_model:
        results = rerank(query, results, reranker_model, reranker_top_k)

    if score_threshold is not None:
        results = apply_threshold(results, score_threshold)

    return results


def retrieve(course: str, query: str) -> RetrievalResults:
    """
    Query ChromaDB and rerank results. Called by the backend.

    Args:
        course: Course unit identifier (e.g., 'ed', 'pp').
        query:  The user's question.

    Returns:
        Structured RetrievalResults object.
    """
    return retrieve_with_config(course, query, score_threshold=RERANKER_SCORE_THRESHOLD)