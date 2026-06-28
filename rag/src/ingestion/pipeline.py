"""Ingestion pipeline for course documents."""

import argparse
import logging
import os
from pathlib import Path

from ..shared.config import COURSE_PATH, KEYWORDS_TO_EXCLUDE, SUPPORTED_EXTENSIONS
from ..shared.utils import extract_metadata_from_filename
from .extractor import extract_elements_from_file, filter_elements, group_elements_by_page
from .chunker import chunk_document
from .embedding import embed_chunks
from ..shared.logging_config import setup_logging

logger = logging.getLogger(__name__)

_REQUIRED_ENV_VARS = [
    "UNSTRUCTURED_API_URL",
    "UNSTRUCTURED_API_KEY",
    "CHROMA_API_KEY",
    "CHROMA_TENANT",
    "CHROMA_DATABASE",
]

def validate_environment() -> None:
    """Validate ingestion environment before processing."""
    missing = [var for var in _REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {missing}")

    search_path = Path(COURSE_PATH)
    if not search_path.exists():
        raise FileNotFoundError(f"COURSE_PATH does not exist: {search_path}")


def process_single_file(
    file_path: Path,
    model_name: str | None = None,
    collection_name: str | None = None,
) -> bool:
    """Process and embed one course document."""
    file_name = file_path.name

    if file_path.stat().st_size == 0:
        logger.warning("Skipping empty file: %s", file_name)
        return False

    try:
        source_type, course_code, _ = extract_metadata_from_filename(file_name)
    except ValueError as e:
        logger.error("Validation failed for '%s': %s", file_name, e)
        return False
    
    try:
        logger.info("--- Processing: %s ---", file_name)

        elements = extract_elements_from_file(str(file_path))

        filtered_elements = filter_elements(elements, KEYWORDS_TO_EXCLUDE)

        grouped_pages = group_elements_by_page(
            filtered_elements,
            source_filename=file_name,
            source_type=source_type,
            course_code=course_code,
            save_images=True
        )

        chunks = chunk_document(grouped_pages)

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
    """Process all supported documents under COURSE_PATH."""
    validate_environment()

    search_path = Path(COURSE_PATH)
    files: list[Path] = [
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

    setup_logging()

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
