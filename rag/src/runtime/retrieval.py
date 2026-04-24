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

from ..shared.config import (
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    RERANKER_TOP_K,
    RETRIEVAL_DISTANCE_THRESHOLD,
    TOP_K_RESULTS,
    TUTOR_FALLBACK_MESSAGE,
)
from ..ingestion.embedding import get_embedder
from ..shared.database import get_collection
from .generator import generate
from .guardrails import (
    detect_code_request,
    detect_prompt_injection,
    sanitize_input,
    validate_input,
)
from ..shared.models import IaEduCredentials, RetrievalResults, TutorResponse
from .reranker import rerank

logger = logging.getLogger(__name__)

def retrieve_with_config(
    course: str,
    query: str,
    *,
    embedding_model: str = EMBEDDING_MODEL,
    top_k: int = TOP_K_RESULTS,
    reranker_model: str | None = RERANKER_MODEL,
    reranker_top_k: int = RERANKER_TOP_K,
    collection_name: str = CHROMA_COLLECTION_NAME,
    distance_threshold: float | None = RETRIEVAL_DISTANCE_THRESHOLD,
) -> RetrievalResults:
    """
    Flexible retrieval for benchmarking. Supports custom embedding models,
    ChromaDB collections, rerankers, and distance thresholds.

    Args:
        course:             Course unit identifier (e.g. 'ed').
        query:              The user's question.
        embedding_model:    HuggingFace model name to embed the query.
        collection_name:    ChromaDB collection to query.
        top_k:              Number of initial candidates to retrieve.
        reranker_model:     Cross-encoder model name, or None to skip reranking.
        reranker_top_k:     Number of results to keep after reranking.
        distance_threshold: Maximum cosine distance allowed. Chunks above this
                            value are dropped before reranking. None disables filtering.

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


def retrieve(course: str, query: str) -> RetrievalResults:
    """
    Query ChromaDB and rerank results. Called by the backend.

    Args:
        course:          Course unit identifier (e.g., 'ed', 'pp').
        query:           The user's question.

    Returns:
        Structured RetrievalResults object.
    """
    return retrieve_with_config(course, query)


def ask(
    course: str,
    query: str,
    summary: str = "",
    history: str = "",
    iaedu_creds: IaEduCredentials | None = None,
) -> TutorResponse:
    """
    End-to-end tutor pipeline: retrieve relevant chunks then generate a Socratic response.

    Applies input guardrails before retrieval. If the query is blocked
    (empty, too short/long, prompt-injection detected, or explicit code
    request), returns early with a rejection message and never hits the LLM.

    Args:
        course:           Course unit identifier (e.g., 'ed', 'pp').
        query:            The student's question.
        summary:          Pre-formatted summary of the conversation.
        history:          Pre-formatted string of the chat history.
        iaedu_creds:  Per-request IAEdu credentials forwarded from the student's
                      frontend session. Required when GENERATOR_BACKEND == "iaedu".

    Returns:
        A TutorResponse with the tutor's answer, cited sources, and fallback flag.
    """
    # 1. Sanitize
    query = sanitize_input(query)

    # 2. Basic length validation
    is_valid, reason = validate_input(query)
    if not is_valid:
        return TutorResponse(answer=reason, sources=[], is_fallback=True, is_guardrail=True)

    # 3. Prompt injection detection
    is_injection, reason = detect_prompt_injection(query)
    if is_injection:
        return TutorResponse(answer=reason, sources=[], is_fallback=True, is_guardrail=True)

    # 4. Code request detection
    is_code_req, reason = detect_code_request(query)
    if is_code_req:
        return TutorResponse(answer=reason, sources=[], is_fallback=True, is_guardrail=True)

    results = retrieve(course, query)

    if results.is_empty():
        logger.warning("[ASK] FALLBACK REASON: no chunks after retrieval (threshold=%.3f).",
                       RETRIEVAL_DISTANCE_THRESHOLD or float("inf"))
        return TutorResponse(
            answer=TUTOR_FALLBACK_MESSAGE,
            sources=[],
            is_fallback=True,
            is_retrieval_fallback=True,
        )

    return generate(
        query,
        results,
        summary,
        history,
        iaedu_creds
    )
