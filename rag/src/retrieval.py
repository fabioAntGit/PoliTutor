"""
Retrieval Module.

This is the primary search execution component of the RAG system. It exposes
functions to fetch and rerank information chunks corresponding
to the user's queries against the ChromaDB document store.

Functions:
    retrieve_with_config: Flexible retrieval for benchmarking with custom parameters.
    retrieve:             Default retrieval using config values. Called by the backend.
    ask:                  End-to-end pipeline: retrieve → generate. Primary backend entry point.
"""

import logging

from .config import (
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    RERANKER_TOP_K,
    TOP_K_RESULTS,
)
from .embedding import get_embedder
from .database import get_collection
from .generator import generate
from .guardrails import (
    detect_code_request,
    detect_prompt_injection,
    sanitize_input,
    validate_input,
)
from .models import RetrievalResults, TutorResponse
from .reranker import rerank

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


def retrieve(course: str, query: str, collection_name: str = CHROMA_COLLECTION_NAME) -> RetrievalResults:
    """
    Query ChromaDB and rerank results. Called by the backend.

    Args:
        course:          Course unit identifier (e.g., 'ed', 'pp').
        query:           The user's question.
        collection_name: ChromaDB collection to query. Defaults to config value.

    Returns:
        Structured RetrievalResults object.
    """
    return retrieve_with_config(course, query, collection_name=collection_name)


def ask(
    course: str,
    query: str,
    *,
    collection_name: str = CHROMA_COLLECTION_NAME,
    iaedu_url: str | None = None,
    iaedu_channel_id: str | None = None,
    iaedu_api_key: str | None = None,
) -> TutorResponse:
    """
    End-to-end tutor pipeline: retrieve relevant chunks then generate a Socratic response.

    Applies input guardrails before retrieval. If the query is blocked
    (empty, too short/long, prompt-injection detected, or explicit code
    request), returns early with a rejection message and never hits the LLM.

    Args:
        course:           Course unit identifier (e.g., 'ed', 'pp').
        query:            The student's question.
        collection_name:  ChromaDB collection to query. Defaults to config value.
        iaedu_url:        IAEdu endpoint. Falls back to env var if not provided.
        iaedu_channel_id: IAEdu channel ID. Falls back to env var if not provided.
        iaedu_api_key:    IAEdu API key. Falls back to env var if not provided.

    Returns:
        A TutorResponse with the tutor's answer, cited sources, and fallback flag.
    """
    # 1. Sanitize
    query = sanitize_input(query)

    # 2. Basic length validation
    is_valid, reason = validate_input(query)
    if not is_valid:
        return TutorResponse(answer=reason, sources=[], is_fallback=True)

    # 3. Prompt injection detection
    is_injection, reason = detect_prompt_injection(query)
    if is_injection:
        return TutorResponse(answer=reason, sources=[], is_fallback=True)

    # 4. Code request detection
    is_code_req, reason = detect_code_request(query)
    if is_code_req:
        return TutorResponse(answer=reason, sources=[], is_fallback=True)

    results = retrieve(course, query, collection_name)
    return generate(query, results, iaedu_url=iaedu_url, iaedu_channel_id=iaedu_channel_id, iaedu_api_key=iaedu_api_key)
