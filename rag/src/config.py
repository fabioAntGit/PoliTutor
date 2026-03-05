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
IMAGES_OUTPUT_DIR = BASE_DIR.parent / "data" / "processed" / "images"

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

# --- Chroma DB Collection
CHROMA_COLLECTION_NAME = "PoliTutor-Docs"

# --- ChromaDB HNSW Index ---
CHROMA_HNSW_SPACE = "cosine"
CHROMA_HNSW_M = 32
CHROMA_HNSW_CONSTRUCTION_EF = 200
CHROMA_HNSW_SEARCH_EF = 100

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

CHUNK_MIN_LENGTH = 100
CHUNK_SEPARATORS = ["```\n", "\n\n", "\n", ". ", "? ", "! ", " ", ""]

VALID_SOURCE_TYPES = set(CHUNKING_STRATEGIES.keys()) - {"default"}

# --- Embedding Configuration ---
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
EMBEDDING_DEVICE = "cpu"
EMBEDDING_NORMALIZE = True

IMAGE_EMBEDDING_PROMPT = (
    "Analyze this image from an educational document. "
    "Set relevant=false ONLY if: "
    "1) The image is a logo or university branding (e.g. P.PORTO, ESTG), a watermark, or purely decorative, OR "
    "2) The image is a tiny fragment of a larger diagram that is too small to convey any meaning on its own "
    "(e.g. a single isolated node, one arrow, one edge of a graph without context). "
    "Everything else is relevant: diagrams, hierarchies, code, formulas, tables, graphs, "
    "flowcharts, trees, UML, algorithms, even partial versions if they still show meaningful structure. "
    "If relevant, write a concise summary in Portuguese. If irrelevant, summary must be empty. "
    'Reply ONLY with raw JSON: {{"relevant": true, "summary": "..."}}'
    "\n\nContext:\n{context}"
)

# --- OpenRouter Image API ---
OPENROUTER_MODEL = "google/gemini-2.0-flash-001"
MAX_IMAGE_API_CALLS = 1  # Limite para testes (None = sem limite)

# --- Retrieval ---
TOP_K_RESULTS: int = 20

# --- Reranker ---
RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
RERANKER_TOP_K: int = 5

# --- Benchmark ---
BENCHMARK_OUTPUT_DIR = BASE_DIR.parent / "data" / "benchmark"
BENCHMARK_MIN_CONTEXT_LENGTH = 200
BENCHMARK_EVAL_METRICS = ["hit_rate@5", "mrr@5", "ndcg@5", "map@5", "precision@5", "recall@5"]
BENCHMARK_PROMPT = (
    "You are an AI engineer specialized in creating benchmark datasets for RAG systems. "
    "Your task is to create a Q&A pair based on the following context. "
    "You MUST base your question and answer SOLELY on the provided context. "
    "Do NOT use any prior memory, or information outside of the given context. "
    "The Q&A pair should be answerable using only the text provided. "
    "Generate the question and answer in Portuguese. "
    "The content is from page {page_number} of {filename} "
    "Reply ONLY with raw JSON, no markdown, no code blocks, no extra text. "
    'Use this exact format: {{"filename": "...", "page": "...", "question": "...", "answer": "..."}}'
    "\n\nContext:\n{context}"
)