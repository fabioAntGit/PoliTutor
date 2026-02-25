"""
Main Pipeline.
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

def process_single_pdf(pdf_path: Path) -> bool:
    """
    Orchestrates the processing pipeline for a single PDF file.

    Args:
        pdf_path: Path object pointing to the source PDF.

    Returns:
        True if processing was successful, False otherwise.
    """
    file_name = pdf_path.name
    file_stem = pdf_path.stem

    if pdf_path.stat().st_size == 0:
        logging.warning(f"Skipping empty file: {file_name}")
        return False

    try:
        source_type, course_code = extract_metadata_from_filename(file_name)
    except ValueError as e:
        logging.error(f"Skipping '{file_name}': {e}")
        return False

    try:
        logging.info(f"Processing: {file_name} | Course: {course_code} | Type: {source_type}")

        elements = extract_elements_from_pdf(str(pdf_path))

        filtered_elements = filter_elements(elements, KEYWORDS_TO_EXCLUDE)
        grouped_pages = group_elements_by_page(
            filtered_elements,
            source_filename=file_name,
            source_type=source_type,
            course_code=course_code,
        )

        chunks = chunk_document(grouped_pages)
        embed_chunks(chunks, file_stem=file_stem)

        logging.info(f"Successfully processed '{file_stem}': {len(chunks)} chunks embedded.")
        return True

    except Exception as e:
        logging.error(f"Failed to process '{file_name}': {str(e)}", exc_info=True)
        return False


def run_pipeline() -> None:
    """
    Main entry point for the pipeline.
    Discovers all PDFs in COURSE_PATH and triggers individual processing.
    """
    pdf_files: List[Path] = list(Path(COURSE_PATH).rglob("*.pdf"))

    if not pdf_files:
        logging.warning(f"No PDF files found in: {COURSE_PATH}")
        return

    logging.info(f"Pipeline started. Found {len(pdf_files)} file(s) to process.")

    success_count = 0
    for pdf_path in pdf_files:
        if process_single_pdf(pdf_path):
            success_count += 1

    logging.info(f"Pipeline finished. {success_count}/{len(pdf_files)} files processed successfully.")


if __name__ == "__main__":
    run_pipeline()