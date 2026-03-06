"""
Main Pipeline Orchestrator.
Discovers, processes, and embeds documents into the RAG system.
"""

import logging
from pathlib import Path
from typing import List

from config import COURSE_PATH, KEYWORDS_TO_EXCLUDE, SUPPORTED_EXTENSIONS
from utils import extract_metadata_from_filename
from pdf_extractor import extract_elements_from_file, filter_elements, group_elements_by_page
from chunker import chunk_document
from embedding import embed_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def process_single_file(file_path: Path) -> bool:
    """
    Orchestrates the full pipeline for a single file.
    From extraction to vector database embedding.
    """
    file_name = file_path.name

    if file_path.stat().st_size == 0:
        logger.warning("Skipping empty file: %s", file_name)
        return False

    # Metadata Extraction & Validation
    try:
        source_type, course_code = extract_metadata_from_filename(file_name)
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
        embed_chunks(chunks, file_stem=file_path.stem)

        logger.info("DONE: '%s' (%d chunks embedded).", file_name, len(chunks))
        return True

    except Exception as e:
        logger.error("Critical error processing '%s': %s", file_name, e, exc_info=True)
        return False

def run_pipeline() -> None:
    """
    Main entry point. Scans COURSE_PATH for files and processes them.
    """
    search_path = Path(COURSE_PATH)
    files: List[Path] = [
        f for ext in SUPPORTED_EXTENSIONS for f in search_path.rglob(ext)
    ]

    if not files:
        logger.warning("No files found in target directory: %s", search_path)
        return

    logger.info("Pipeline started. Found %d file(s) in %s", len(files), search_path.name)

    success_count = 0
    for file_path in files:
        if process_single_file(file_path):
            success_count += 1

    logger.info("Pipeline finished. Successfully processed %d/%d files.", success_count, len(files))

if __name__ == "__main__":
    run_pipeline()