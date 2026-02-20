"""
Main Pipeline.
"""

import logging
from pathlib import Path
from typing import List, Optional

# Internal imports
from config import (
    COURSE_PATH,
    OUTPUT_DIR,
    OUTPUT_DIR_BEFORE,
    KEYWORDS_TO_EXCLUDE,
    OUTPUT_DIR_CHUNKS,
)
from utils import extract_source_type
from pdf_extractor import (
    extract_elements_from_pdf,
    filter_elements,
    group_elements_by_page,
    save_json,
)
from chunker import chunk_document, save_chunks

# Logging Configuration
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def ensure_environment() -> None:
    """
    Initializes the required directory structure.
    Ensures all output folders exist before processing starts.
    """
    directories = [OUTPUT_DIR, OUTPUT_DIR_BEFORE, OUTPUT_DIR_CHUNKS]
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

def process_single_pdf(pdf_path: Path) -> bool:
    """
    Orchestrates the processing pipeline for a single PDF file.
    
    Args:
        pdf_path (Path): Path object pointing to the source PDF.
        
    Returns:
        bool: True if processing was successful, False otherwise.
    """
    file_name = pdf_path.name        # e.g., "2024.ED.Aula01.pdf"
    file_stem = pdf_path.stem        # e.g., "2024.ED.Aula01"
    
    try:
        # 1. Source Identification
        source_type = extract_source_type(str(pdf_path))
        logging.info(f"Processing: {file_name} (Source: {source_type})")

        # 2. Raw Extraction (Stage: Before)
        elements = extract_elements_from_pdf(str(pdf_path))
        raw_output = Path(OUTPUT_DIR_BEFORE) / f"{file_stem}_raw.json"
        save_json(elements, str(raw_output))

        # 3. Filtering & Grouping (Stage: Processed)
        # Removes headers/footers and organizes content by page
        filtered_elements = filter_elements(elements, KEYWORDS_TO_EXCLUDE)
        grouped_pages = group_elements_by_page(
            filtered_elements,
            source_filename=file_name,
            source_type=source_type,
        )
        processed_output = Path(OUTPUT_DIR) / f"{file_stem}.json"
        save_json(grouped_pages, str(processed_output))

        # 4. Chunking (Stage: Chunks)
        chunks = chunk_document(grouped_pages)
        chunks_output = Path(OUTPUT_DIR_CHUNKS) / f"{file_stem}_chunks.json"
        save_chunks(chunks, str(chunks_output))

        logging.info(f"✓ Successfully processed {file_stem}: {len(chunks)} chunks generated.")
        return True

    except Exception as e:
        logging.error(f"✗ Failed to process {file_name}: {str(e)}", exc_info=True)
        return False

def run_pipeline() -> None:
    """
    Main entry point for the pipeline.
    Discovers all PDFs in COURSE_PATH and triggers individual processing.
    """
    ensure_environment()
    
    pdf_files: List[Path] = list(Path(COURSE_PATH).rglob("*.pdf"))

    if not pdf_files:
        logging.warning(f"No PDF files found in directory: {COURSE_PATH}")
        return

    logging.info(f"Pipeline started. Found {len(pdf_files)} files to process.")
    
    success_count = 0
    for pdf_path in pdf_files:
        if process_single_pdf(pdf_path):
            success_count += 1

    logging.info(
        f"Pipeline finished. Status: {success_count}/{len(pdf_files)} files processed successfully."
    )

if __name__ == "__main__":
    run_pipeline()