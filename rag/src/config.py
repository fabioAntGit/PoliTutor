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

# --- Extraction & Filtering Settings ---
# Keywords to discard
KEYWORDS_TO_EXCLUDE = [
    "Ricardo Santos",
    "rjs@estg.ipp.pt",
    "Escola Superior de Tecnologia e Gestão Instituto Politécnico do Porto",
    "ESTRUTURAS DE DADOS 2024/2025",
]

# Unstructured element types to completely remove from the pipeline
ELEMENT_TYPES_TO_EXCLUDE = [
    "Footer",
    "Header",
    "FigureCaption",
    "UncategorizedText"
]

# Valid source types extracted from filenames (e.g. "Slides.ED.CAP1.pdf" -> "slides")
# Add new source types here as new document categories are introduced.
VALID_SOURCE_TYPES = {"apontamentos", "slides"}

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
CHROMA_COLLECTION_NAME = "PoliTutor-Docs4"