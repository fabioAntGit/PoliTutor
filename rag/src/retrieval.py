import logging
from typing import Dict, Any

from config import CHROMA_COLLECTION_NAME, TOP_K_RESULTS
from embedding import get_embedder, connect_chromadb

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

EXIT_COMMANDS = {'exit', 'quit', 'q'}

def retrieval() -> None:
    """Interactive CLI to query ChromaDB using the embedding model."""
    try:
        collection = connect_chromadb()
        embedder = get_embedder()
        course_unit = prompt_course_unit()
        run_query_loop(collection, embedder, course_unit)

    except Exception as e:
        logger.error("An error occurred during retrieval: %s", e)

def prompt_course_unit() -> str:
    return input("\nEnter the Course Unit (UC) to search (e.g., ED, PP): ").strip().lower()

def run_query_loop(collection, embedder, course_unit: str) -> None:
    while True:
        query = input("\nEnter your question (or type 'exit' to quit): ").strip()

        if query.lower() in EXIT_COMMANDS:
            print("Exiting retrieval CLI...")
            break

        if not query:
            continue

        results = query_collection(collection, embedder, query, course_unit)
        display_results(results, course_unit)

def query_collection(collection, embedder, query: str, course_unit: str) -> Dict[str, Any]:
    logger.info("Generating embedding for your query...")
    query_vector = embedder.embed_query(query)

    return collection.query(
        query_embeddings=[query_vector],
        n_results=TOP_K_RESULTS,
        where={"course": course_unit},
    )

def display_results(results: Dict[str, Any], course_unit: str) -> None:
    """Parses and prints the results from ChromaDB."""
    ids = results.get('ids', [[]])[0]
    documents = results.get('documents', [[]])[0]
    metadatas = results.get('metadatas', [[]])[0]
    distances = results.get('distances', [[]])[0]

    if not ids:
        print(f"\nNo relevant chunks found for UC '{course_unit}'. Make sure the metadata 'course' matches exactly.")
        return

    print(f"\nFound {len(ids)} relevant chunks for '{course_unit}':")

    for rank, (doc_id, document, metadata, distance) in enumerate(zip(ids, documents, metadatas, distances), start=1):
        print_result(rank, doc_id, document, metadata, distance)
        
def print_result(rank: int, doc_id: str, document: str, metadata: Dict[str, Any], distance: float) -> None:
    similarity_score = 1 - distance
    filename = metadata.get('filename', 'Unknown')
    source_type = metadata.get('source', 'Unknown')
    page = metadata.get('pages', 'N/A')
    content_preview = document

    print(f"RANK #{rank} | Similarity Score: {similarity_score:.4f} | ID: {doc_id}")
    print(f"Source: {source_type} | File: {filename} | Page: {page}")
    print(f"Content: {content_preview}...")
    print("-" * 60)


if __name__ == "__main__":
    retrieval()