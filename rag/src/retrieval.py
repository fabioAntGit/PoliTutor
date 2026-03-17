"""
Retrieval Module.

This is the primary search execution component of the RAG system. It exposes
functions to fetch and rerank information chunks corresponding
to the user's queries against the ChromaDB document store.
"""

import logging

from config import (
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    RERANKER_TOP_K,
    TOP_K_RESULTS,
)
from embedding import get_embedder
from database import get_collection
from models import RetrievalResults
from reranker import rerank

logger = logging.getLogger(__name__)

def retrieve_with_config(
    course: str,
    query: str,
    *,
    embedding_model: str = EMBEDDING_MODEL,
    collection_name: str = CHROMA_COLLECTION_NAME,
    top_k: int = TOP_K_RESULTS,
    reranker_model: str | None = RERANKER_MODEL,
    reranker_top_k: int = RERANKER_TOP_K,
) -> RetrievalResults:
    """
    Flexible retrieval for benchmarking. Supports custom embedding models,
    ChromaDB collections, and rerankers.

    Args:
        course:           Course unit identifier (e.g. 'ed').
        query:            The user's question.
        embedding_model:  HuggingFace model name to embed the query.
        collection_name:  ChromaDB collection to query.
        top_k:            Number of initial candidates to retrieve.
        reranker_model:   Cross-encoder model name, or None to skip reranking.
        reranker_top_k:   Number of results to keep after reranking.

    Returns:
        Structured RetrievalResults with aligned arrays of ids, documents, metadatas, distances, scores.
    """
    collection = get_collection(collection_name)
    embedder = get_embedder(embedding_model)

    query_vector = embedder.embed_query(query)

    raw = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        where={"course": course.strip().lower()},
    )

    results = RetrievalResults.from_chroma_dict(raw)

    if reranker_model:
        results = rerank(query, results, reranker_model, reranker_top_k)

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
    return retrieve_with_config(course, query)