"""
Main Pipeline Orchestrator.

Acts as the entry point for the RAG data ingestion process. Discovers documents,
extracts text and images, creates vector embeddings using HuggingFace models,
and stores the chunks into the ChromaDB cloud instance.
Supports custom models and collections via CLI for benchmarking purposes.
"""

import argparse
import logging
from pathlib import Path
from typing import List

from config import COURSE_PATH, KEYWORDS_TO_EXCLUDE, SUPPORTED_EXTENSIONS
from utils import extract_metadata_from_filename
from extractor import extract_elements_from_file, filter_elements, group_elements_by_page
from chunker import chunk_document
from embedding import embed_chunks

logger = logging.getLogger(__name__)

def process_single_file(
    file_path: Path,
    model_name: str | None = None,
    collection_name: str | None = None,
) -> bool:
    """
    Orchestrates the full RAG ingestion pipeline for a single file.

    Process:
        1. Validates the filename conventions.
        2. Extracts raw text elements and images via Unstructured API.
        3. Groups elements contextually by page.
        4. Splits pages into smaller, semantically preserving chunks.
        5. Embeds the chunks along with AI-generated image summaries.

    Args:
        file_path (Path): Path to the single document file to process.
        model_name (str | None): HuggingFace embedding model. Uses config default if None.
        collection_name (str | None): ChromaDB collection name. Uses config default if None.
        
    Returns:
        bool: True if the file was processed and embedded successfully, False if it failed
              or was skipped due to validation errors.
    """
    file_name = file_path.name

    if file_path.stat().st_size == 0:
        logger.warning("Skipping empty file: %s", file_name)
        return False

    # Metadata Extraction & Validation
    try:
        source_type, course_code, stem = extract_metadata_from_filename(file_name)
    except ValueError as e:
        logger.error("Validation failed for '%s': %s", file_name, e)
        return False
    
    # Document Processing
    try:
        logger.info("--- Processing: %s ---", file_name)

        elements = extract_elements_from_file(str(file_path))

        filtered_elements = filter_elements(elements, KEYWORDS_TO_EXCLUDE)

        # Group by page with context
        grouped_pages = group_elements_by_page(
            filtered_elements,
            source_filename=file_name,
            source_type=source_type,
            course_code=course_code,
            save_images=True
        )

        # Segment into chunks
        chunks = chunk_document(grouped_pages)

        # Embedding and Vector Storage
        embed_chunks(
            chunks,
            file_stem=file_path.stem,
            model_name=model_name,
            collection_name=collection_name,
        )

        logger.info("DONE: '%s' (%d chunks embedded).", file_name, len(chunks))
        return True

    except Exception as e:
        logger.error("Critical error processing '%s': %s", file_name, e, exc_info=True)
        return False

def run_pipeline(
    model_name: str | None = None,
    collection_name: str | None = None,
) -> None:
    """
    Main entry point. Scans COURSE_PATH for files and processes them.

    Args:
        model_name:      HuggingFace embedding model. Uses default if None.
        collection_name: ChromaDB collection name. Uses default if None.
    """
    search_path = Path(COURSE_PATH)
    files: List[Path] = [
        f for ext in SUPPORTED_EXTENSIONS for f in search_path.rglob(ext)
    ]

    if not files:
        logger.warning("No files found in target directory: %s", search_path)
        return

    target_info = f"model={model_name or 'default'}, collection={collection_name or 'default'}"
    logger.info("Pipeline started. Found %d file(s) in %s (%s)", len(files), search_path.name, target_info)

    success_count = 0
    for file_path in files:
        if process_single_file(file_path, model_name, collection_name):
            success_count += 1

    logger.info("Pipeline finished. Successfully processed %d/%d files.", success_count, len(files))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Pipeline Orchestrator")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="HuggingFace embedding model name (e.g. 'BAAI/bge-m3'). Uses config default if omitted.",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=None,
        help="ChromaDB collection name (e.g. 'PoliTutor-Docs-bge-m3'). Uses config default if omitted.",
    )
    args = parser.parse_args()
    run_pipeline(model_name=args.model, collection_name=args.collection)