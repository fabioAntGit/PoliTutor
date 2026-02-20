"""
Configuration settings
"""

import os
from pathlib import Path

# --- Path Management ---
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_RAW_PATH = BASE_DIR.parent / "data" / "raw"

# Root path for raw data
RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", DEFAULT_RAW_PATH))

# Course-specific source and output directories
COURSE_PATH = Path(os.getenv("COURSE_PATH", RAW_DATA_PATH / "ED"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", RAW_DATA_PATH / "processed_json"))
OUTPUT_DIR_BEFORE = Path(os.getenv("OUTPUT_DIR_BEFORE", RAW_DATA_PATH / "processedBefore_json"))
OUTPUT_DIR_CHUNKS = Path(os.getenv("OUTPUT_DIR_CHUNKS", RAW_DATA_PATH / "chunked_json"))

# --- Extraction & Filtering Settings ---
# Keywords to discard
KEYWORDS_TO_EXCLUDE = [
    "Ricardo Santos",
    "rjs@estg.ipp.pt",
    "Escola Superior de Tecnologia e Gestão Instituto Politécnico do Porto",
]

# Unstructured element types to completely remove from the pipeline
ELEMENT_TYPES_TO_EXCLUDE = [
    "Footer",
    "Header",
]

# Elements that exist but should not be rendered as plain text
ELEMENT_TYPES_TO_SKIP_IN_TEXT = [
    "Image",
]

# --- Unstructured Partitioning Configuration ---
PDF_PROCESSING_CONFIG = {
    "strategy": "hi_res",
    "infer_table_structure": True,
    "extract_image_block_types": ["Image", "Table"],
    "extract_images_in_pdf": True,
    "extract_image_block_to_payload": True,
    "chunking_strategy": None, 
    "include_orig_elements": False,
}

# --- Text Chunking Configuration ---
CHUNKING_CONFIG = {
    "chunk_size": 2000,
    "chunk_overlap": 200,
}