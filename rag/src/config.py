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
        "chunk_size": 1000,
        "chunk_overlap": 150,
    },
    "slides": {
        "chunk_size": 600,
        "chunk_overlap": 100,
    },
    "default": {
        "chunk_size": 700,
        "chunk_overlap": 100,
    }
}

VALID_SOURCE_TYPES = set(CHUNKING_STRATEGIES.keys()) - {"default"}

# --- Embedding Configuration ---
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
CHROMA_COLLECTION_NAME = "PoliTutor-Docs"

# --- Retrieval ---
TOP_K_RESULTS: int = 20

# --- Reranker ---
RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
RERANKER_TOP_K: int = 5

# --- Benchmark ---
BENCHMARK_OUTPUT_DIR = BASE_DIR.parent / "data" / "benchmark"
BENCHMARK_PROMPT = (
    "You are an AI engineer specialized in creating benchmark datasets for RAG systems. "
    "Your task is to create a Q&A pair based on the following context. "
    "You MUST base your question and answer SOLELY on the provided context. "
    "Do NOT use any prior memory, or information outside of the given context. "
    "The Q&A pair should be answerable using only the text provided. "
    "The content is from page {page_number} of {filename} "
    "Reply ONLY with raw JSON, no markdown, no code blocks, no extra text. "
    'Use this exact format: {{"filename": "...", "page": "...", "question": "...", "answer": "..."}}'
    "\n\nContext:\n{context}"
)