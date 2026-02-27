"""
Retrieval module.
Exposes retrieve() to be called by a backend, keeping the original working logic.
"""

import logging
from typing import Dict, Any

from config import TOP_K_RESULTS
from embedding import get_embedder
from database import get_collection

from reranker import rerank

logger = logging.getLogger(__name__)

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