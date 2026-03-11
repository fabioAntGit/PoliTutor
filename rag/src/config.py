"""
Configuration settings for the Poli-Tutor RAG pipeline.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# 1. CORE & ENVIRONMENT INITIALIZATION
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

BASE_DIR = Path(__file__).resolve().parent
# Load environment variables from the root .env file
load_dotenv(BASE_DIR.parent / ".env")

# 2. PATH MANAGEMENT
DEFAULT_RAW_PATH = BASE_DIR.parent / "data" / "raw"
RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", DEFAULT_RAW_PATH))
COURSE_PATH = Path(os.getenv("COURSE_PATH", RAW_DATA_PATH / "ED"))
IMAGES_OUTPUT_DIR = BASE_DIR.parent / "data" / "processed" / "images"

# 3. DOCUMENT EXTRACTION (Unstructured API)
SUPPORTED_EXTENSIONS = ["*.pdf", "*.pptx", "*.md"]

# Text elements and phrases to ignore during ingestion
ELEMENT_TYPES_TO_EXCLUDE = ["Footer", "Header", "FigureCaption", "UncategorizedText"]
KEYWORDS_TO_EXCLUDE = [
    "Ricardo Santos",
    "rjs@estg.ipp.pt",
    "Escola Superior de Tecnologia e Gestão Instituto Politécnico do Porto",
    "ESTRUTURAS DE DADOS 2024/2025",
]

# Unstructured API parameters
FILE_PROCESSING_CONFIG = {
    "strategy": "hi_res",
    "languages": ["por", "eng"],
    "infer_table_structure": True,
    "extract_image_block_types": ["Image"],
    "extract_image_block_to_payload": True,
    "chunking_strategy": None,
    "skip_infer_table_types": ["md"],
}

# 4. CHUNKING STRATEGIES
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
CHUNK_SEPARATORS = ["```\n", "\n\n", "\n", ". ", "? ", "! ", " ", ""]
CHUNK_MIN_LENGTH = 100
VALID_SOURCE_TYPES = set(CHUNKING_STRATEGIES.keys()) - {"default"}

# 5. EMBEDDING & IMAGE ANALYSIS
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
EMBEDDING_DEVICE = "cpu"
EMBEDDING_NORMALIZE = True

# Image summarization (OpenRouter/Gemini)
OPENROUTER_MODEL = "google/gemini-2.5-flash-lite"
MAX_IMAGE_API_CALLS = None  # No limit
IMAGE_API_DELAY = 1.5

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

# 6. VECTOR DATABASE (ChromaDB)
CHROMA_COLLECTION_NAME = "PoliTutor-Docs-e5-large"

# Low-level HNSW tuning
CHROMA_HNSW_SPACE = "cosine"
CHROMA_HNSW_M = 32
CHROMA_HNSW_CONSTRUCTION_EF = 200
CHROMA_HNSW_SEARCH_EF = 100

# 7. RETRIEVAL & RERANKING
TOP_K_RESULTS = 20
RERANKER_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
RERANKER_TOP_K = 5
RERANKER_SCORE_THRESHOLD = 0.0

# 8. BENCHMARKING & EVALUATION
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

# Configuration comparison for sweep benchmarks
BENCHMARK_COMPARISON_CONFIGS = [
    {
        "name": "e5-large + mMiniLM",
        "embedding_model": "intfloat/multilingual-e5-large",
        "collection_name": "PoliTutor-Docs-e5-large",
        "reranker_model": "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
    }
]

BENCHMARK_THRESHOLD_SWEEP = {
    "start": -4.0,
    "stop":   4.0,
    "step":   0.25,
    "primary_metric": "ndcg@5",
}