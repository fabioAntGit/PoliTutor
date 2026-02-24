"""
Configuration settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# --- Path Management ---
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")
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
    "FigureCaption",
    "UncategorizedText"
]

# --- Unstructured Partitioning Configuration ---
PDF_PROCESSING_CONFIG = {
    "strategy": "hi_res",
    "languages": ["por", "eng"],
    "infer_table_structure": True,
    "extract_image_block_types": ["Image"],
    "extract_image_block_to_payload": True,
    "chunking_strategy": None, 
}

# --- Chunking Configuration ---
CHUNKING_CONFIG_APONTAMENTOS = {
    "chunk_size": 800,
    "chunk_overlap": 100,
}

CHUNKING_CONFIG_SLIDES = {
    "chunk_size": 400,
    "chunk_overlap": 50,
}

# --- Embedding Configuration ---
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
