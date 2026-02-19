"""
Main pipeline
"""
import os
import glob
import logging
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

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def process_all_pdfs() -> None:
    """
    Iterates over all PDFs found under COURSE_PATH and for each one:
      1. Extracts raw elements and saves them to OUTPUT_DIR_BEFORE (for debugging)
      2. Filters out unwanted elements
      3. Groups by page and saves the final JSON to OUTPUT_DIR
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR_BEFORE, exist_ok=True)

    pdf_files = glob.glob(os.path.join(COURSE_PATH, "**", "*.pdf"), recursive=True)
    if not pdf_files:
        logging.warning(f"No PDFs found in: {COURSE_PATH}")
        return

    for pdf_path in pdf_files:
        file_name = os.path.basename(pdf_path)
        file_stem = os.path.splitext(file_name)[0]
        source_type = extract_source_type(pdf_path)
        logging.info(f"Processing: {file_name}...")

        try:
            elements = extract_elements_from_pdf(pdf_path)

            # Save raw elements for analysis/debugging
            before_path = os.path.join(OUTPUT_DIR_BEFORE, f"{file_stem}Before.json")
            save_json(elements, before_path)

            filtered_elements = filter_elements(elements, KEYWORDS_TO_EXCLUDE)
            n_filtered = len(elements) - len(filtered_elements)

            grouped_pages = group_elements_by_page(
                filtered_elements,
                source_filename=file_name,
                source_type=source_type,
            )
            output_path = os.path.join(OUTPUT_DIR, f"{file_stem}.json")
            save_json(grouped_pages, output_path)

            # Chunk pages into embedding-ready format
            chunks = chunk_document(grouped_pages)
            chunks_path = os.path.join(OUTPUT_DIR_CHUNKS, f"{file_stem}.json")
            save_chunks(chunks, chunks_path)

            logging.info(
                f"Done: {file_stem} — "
                f"{len(grouped_pages)} pages, "
                f"{len(chunks)} chunks, "
                f"{n_filtered} elements filtered out."
            )

        except Exception as e:
            logging.error(f"Error processing {file_name}: {e}")


if __name__ == "__main__":
    process_all_pdfs()