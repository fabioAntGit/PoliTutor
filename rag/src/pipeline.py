"""
Main Pipeline Orchestrator.
Discovers, processes, and embeds PDF documents into the RAG system.
"""

import logging
from pathlib import Path
from typing import List

from config import COURSE_PATH, KEYWORDS_TO_EXCLUDE
from utils import extract_metadata_from_filename
from pdf_extractor import extract_elements_from_pdf, filter_elements, group_elements_by_page
from chunker import chunk_document
from embedding import embed_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def process_single_pdf(pdf_path: Path) -> bool:
    """
    Orchestrates the full pipeline for a single PDF.
    From extraction to vector database embedding.
    """
    file_name = pdf_path.name

    if pdf_path.stat().st_size == 0:
        logger.warning(f"Skipping empty file: {file_name}")
        return False

    # Metadata Extraction & Validation
    try:
        source_type, course_code = extract_metadata_from_filename(file_name)
    except ValueError as e:
        logger.error(f"Validation failed for '{file_name}': {e}")
        return False
    
    # Document Processing
    try:
        logger.info(f"--- Processing: {file_name} ---")

        elements = extract_elements_from_pdf(str(pdf_path))

        filtered_elements = filter_elements(elements, KEYWORDS_TO_EXCLUDE)

        # Group by page with context
        grouped_pages = group_elements_by_page(
            filtered_elements,
            source_filename=file_name,
            source_type=source_type,
            course_code=course_code,
        )

        # Segment into chunks
        chunks = chunk_document(grouped_pages)

        # Embedding and Vector Storage
        embed_chunks(chunks, file_stem=pdf_path.stem)

        logger.info(f"DONE: '{file_name}' ({len(chunks)} chunks embedded).")
        return True

    except Exception as e:
        logger.error(f"Critical error processing '{file_name}': {e}", exc_info=True)
        return False

def run_pipeline() -> None:
    """
    Main entry point. Scans COURSE_PATH for PDFs and processes them.
    """
    search_path = Path(COURSE_PATH)
    pdf_files: List[Path] = list(search_path.rglob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDF files found in target directory: {search_path}")
        return

    logger.info(f"Pipeline started. Found {len(pdf_files)} file(s) in {search_path.name}")

    success_count = 0
    for pdf_path in pdf_files:
        if process_single_pdf(pdf_path):
            success_count += 1

    logger.info(f"Pipeline finished. Successfully processed {success_count}/{len(pdf_files)} files.")

if __name__ == "__main__":
    run_pipeline()