"""
Configuration settings for the RAG pipeline.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# --- Path Management ---
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / ".env")

# Default paths
DEFAULT_RAW_PATH = BASE_DIR.parent / "data" / "raw"
RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", DEFAULT_RAW_PATH))

# Specific course directory
COURSE_PATH = Path(os.getenv("COURSE_PATH", RAW_DATA_PATH / "ED"))

# --- Extraction & Filtering Settings ---
KEYWORDS_TO_EXCLUDE = [
    "Ricardo Santos",
    "rjs@estg.ipp.pt",
    "Escola Superior de Tecnologia e Gestão Instituto Politécnico do Porto",
    "ESTRUTURAS DE DADOS 2024/2025",
]

# Unstructured elements to ignore
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

# --- Chunking & Source Mapping ---
CHUNKING_STRATEGIES = {
    "apontamentos": {
        "chunk_size": 800,
        "chunk_overlap": 100,
    },
    "slides": {
        "chunk_size": 400,
        "chunk_overlap": 50,
    },
    "default": {
        "chunk_size": 500,
        "chunk_overlap": 50,
    }
}

VALID_SOURCE_TYPES = set(CHUNKING_STRATEGIES.keys()) - {"default"}

# --- Embedding Configuration ---
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
CHROMA_COLLECTION_NAME = "PoliTutor-Docs4"

# --- Retrieval ---

TOP_K_RESULTS: int = 5