"""
Retrieval module.
Exposes retrieve() to be called by a backend, keeping the original working logic.
"""

import logging
from typing import Dict, Any

from config import TOP_K_RESULTS, EMBEDDING_MODEL, CHROMA_COLLECTION_NAME, RERANKER_MODEL, RERANKER_TOP_K
from embedding import get_embedder, get_embedder_for_model
from database import get_collection, get_collection_by_name
from reranker import rerank, rerank_with_model

logger = logging.getLogger(__name__)

def apply_threshold(results: Dict[str, Any], threshold: float) -> Dict[str, Any]:
    """Removes chunks whose score is below `threshold`."""
    ids       = results.get("ids",       [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    scores    = results.get("scores",    [[]])[0]

    kept = [(i, d, m, dist, s) for i, d, m, dist, s in
            zip(ids, documents, metadatas, distances, scores) if s >= threshold]

    if not kept:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]], "scores": [[]]}

    ids_f, docs_f, metas_f, dists_f, scores_f = zip(*kept)
    return {
        "ids":       [list(ids_f)],
        "documents": [list(docs_f)],
        "metadatas": [list(metas_f)],
        "distances": [list(dists_f)],
        "scores":    [list(scores_f)],
    }


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
        ChromaDB-style dict with keys: ids, documents, metadatas, distances, scores.
    """
    collection = get_collection_by_name(collection_name)
    embedder   = get_embedder_for_model(embedding_model)

    query_vector = embedder.embed_query(query)

    raw = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
        where={"course": course.strip().lower()},
    )

    if reranker_model:
        results = rerank_with_model(query, raw, reranker_model, reranker_top_k)
    else:
        distances = raw.get("distances", [[]])[0]
        raw["scores"] = [[1.0 - d for d in distances]]
        results = raw

    if score_threshold is not None:
        results = apply_threshold(results, score_threshold)

    return results


def retrieve(course: str, query: str) -> Dict[str, Any]:
    """
    Query ChromaDB and rerank results. Called by the backend.

    Args:
        course: Course unit identifier (e.g., 'ed', 'pp').
        query:  The user's question.

    Returns:
        ChromaDB-style dict with keys: ids, documents, metadatas, distances, scores.
    """
    collection = get_collection()
    embedder = get_embedder()

    query_vector = embedder.embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=TOP_K_RESULTS,
        where={"course": course.strip().lower()},
    )

    return rerank(query, results)

# ── CLI (for local testing)

EXIT_COMMANDS = {'exit', 'quit', 'q'}

def cli() -> None:
    """
    Interactive CLI for testing the retrieval pipeline locally.

    Prompts the user for a course unit, then enters a loop accepting
    free-text queries until an exit command is issued.
    """
    try:
        course_unit = input("\nEnter the Course Unit (UC) to search (e.g., ED, PP): ").strip().lower()

        while True:
            query = input("\nEnter your question (or type 'exit' to quit): ").strip()

            if query.lower() in EXIT_COMMANDS:
                print("Exiting retrieval CLI...")
                break

            if not query:
                continue

            results = retrieve(course_unit, query)
            display_results(results, course_unit)

    except Exception as e:
        logger.error("An error occurred during retrieval: %s", e)

def display_results(results: Dict[str, Any], course_unit: str) -> None:
    """
    Print reranked retrieval results.
    """
    ids       = results.get('ids',       [[]])[0]
    documents = results.get('documents', [[]])[0]
    metadatas = results.get('metadatas', [[]])[0]
    distances = results.get('distances', [[]])[0]

    if not ids:
        print(f"\nNo relevant chunks found for UC '{course_unit}'. Make sure the metadata 'course' matches exactly.")
        return

    print(f"\nFound {len(ids)} relevant chunks for '{course_unit}':")

    for rank, (doc_id, document, metadata, distance) in enumerate(zip(ids, documents, metadatas, distances), start=1):
        similarity_score = 1 - distance
        print(f"RANK #{rank} | Similarity Score: {similarity_score:.4f} | ID: {doc_id}")
        print(f"Source: {metadata.get('source', 'Unknown')} | File: {metadata.get('filename', 'Unknown')} | Page: {metadata.get('pages', 'N/A')}")
        print(f"Content: {document}...")
        print("-" * 60)

if __name__ == "__main__":
    cli()