"""Configuration for the Poli-Tutor RAG pipeline."""

import os
import torch
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
RAG_DIR = BASE_DIR.parent.parent  # rag/
load_dotenv(RAG_DIR / ".env")

DEFAULT_RAW_PATH = RAG_DIR / "data" / "raw"
RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", DEFAULT_RAW_PATH))
COURSE_PATH = Path(os.getenv("COURSE_PATH", RAW_DATA_PATH / "ED"))
IMAGES_OUTPUT_DIR = RAG_DIR / "data" / "processed" / "images"

SUPPORTED_EXTENSIONS = ["*.pdf", "*.pptx", "*.md"]

ELEMENT_TYPES_TO_EXCLUDE = ["Footer", "Header", "FigureCaption", "UncategorizedText"]
KEYWORDS_TO_EXCLUDE = [
    "Ricardo Santos",
    "rjs@estg.ipp.pt",
    "Escola Superior de Tecnologia e Gestão Instituto Politécnico do Porto",
    "ESTRUTURAS DE DADOS 2024/2025",
]

FILE_PROCESSING_CONFIG = {
    "strategy": "hi_res",
    "languages": ["por", "eng"],
    "infer_table_structure": True,
    "extract_image_block_types": ["Image"],
    "extract_image_block_to_payload": True,
    "chunking_strategy": None,
    "skip_infer_table_types": ["md"],
}

CHUNKING_STRATEGIES = {
    "apontamentos": {
        "chunk_size": 300,
        "chunk_overlap": 150,
    },
    "slides": {
        "chunk_size": 300,
        "chunk_overlap": 250,
    },
    "default": {
        "chunk_size": 300,
        "chunk_overlap": 200,
    }
}
CHUNK_SEPARATORS = ["```\n", "\n\n", "\n", ". ", "? ", "! ", " ", ""]
CHUNK_MIN_LENGTH = 100
VALID_SOURCE_TYPES = set(CHUNKING_STRATEGIES.keys()) - {"default"}

# Benchmark-selected embedding model; ingestion and retrieval must match.
EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else ("mps" if torch.backends.mps.is_available() else "cpu")
)
EMBEDDING_NORMALIZE = True

OPENROUTER_MODEL_IMAGE_SUMMARIZATION = "google/gemini-2.5-flash-lite"
OPENROUTER_MODEL_BENCHMARK = "openai/gpt-4o"
OPENROUTER_MODEL_GENERATOR = "openai/gpt-4o"

TUTOR_TEMPERATURE = 0.7

MAX_IMAGE_API_CALLS = None  # No limit
IMAGE_API_DELAY = 1.5

CHROMA_COLLECTION_NAME = "PoliTutor-Docs"
CHROMA_METADATA = {"hnsw:space": "cosine"}

TOP_K_RESULTS = 20
RERANKER_MODEL = "jinaai/jina-reranker-v2-base-multilingual"
RERANKER_TOP_K = 5
# Calibrated via benchmark_threshold.py; None disables distance filtering.
RETRIEVAL_DISTANCE_THRESHOLD: float | None = 0.9301

BENCHMARK_OUTPUT_DIR = RAG_DIR / "data" / "benchmark"
BENCHMARK_MIN_CONTEXT_LENGTH = 200
TUTOR_BENCHMARK_MAX_QUESTIONS = 200  # Max questions to generate (2 per sampled page: 1 regular + 1 adversarial)

BENCHMARK_EVAL_METRICS = [
    "hit_rate@5",
    "mrr@5",
    "ndcg@5",
    "map@5",
    "precision@5",
    "recall@5",
]

# Omitted fields use BenchmarkConfig defaults.
BENCHMARK_COMPARISON_CONFIGS = [
    {
        "name": "bge-m3 + jinaai jina-reranker-v2-base-multilingual",
        "embedding_model": "BAAI/bge-m3",
        "collection_name": "PoliTutor-Docs-bge-m3",
        "reranker_model": "jinaai/jina-reranker-v2-base-multilingual",
    },
    {
        "name": "bge-m3 +  BAAI bge-reranker-base",
        "embedding_model": "BAAI/bge-m3",
        "collection_name": "PoliTutor-Docs-bge-m3",
        "reranker_model": "BAAI/bge-reranker-base",
    },
    {
        "name": "bge-m3 + Alibaba-NLP gte-reranker-modernbert-base",
        "embedding_model": "BAAI/bge-m3",
        "collection_name": "PoliTutor-Docs-bge-m3",
        "reranker_model": "Alibaba-NLP/gte-reranker-modernbert-base",
    }
]

QUERY_MIN_LENGTH = 2
QUERY_MAX_LENGTH = 1500
# Long answers without a guiding question are treated as direct answers.
DIRECT_ANSWER_MIN_LENGTH = 100

INJECTION_PATTERNS: list[str] = [
    r"ignora(?:r)? .*instru[çc][õo]es?",
    r"ignore .*instructions?",
    r"ignore .*previous instructions?",
    r"esquece .*regras?",
    r"forget .*rules?",
    r"ignora(?:r)? o sistema",
    r"ignore the system",
    r"prompt de sistema",
    r"system prompt",
    r"prompt de desenvolvedor",
    r"developer prompt",
    r"modo desenvolvedor",
    r"developer mode",
    r"atua como",
    r"age como",
    r"finge que",
    r"faz de conta",
    r"act as",
    r"behave as",
    r"pretend(?: to be)?",
    r"d[áa][-\s]?me a resposta",
    r"diz[-\s]?me a resposta",
    r"d[áa][-\s]?me o c[óo]digo",
    r"d[áa][-\s]?me a solu[çc][ãa]o",
    r"quero apenas a resposta",
    r"mostra(?:r)? a resposta final",
    r"dá[-\s]?me a resposta final",
    r"give me the (?:answer|code|solution)",
    r"just give me the answer",
    r"show me the final answer",
    r"give me the final answer",
    r"i only want the answer",
    r"n[ãa]o (sejas|seja) socr[áa]tico",
    r"p[áa]ra de ser socr[áa]tico",
    r"sem explica[çc][õo]es?",
    r"sem passos",
    r"sem dicas",
    r"don't be socratic",
    r"stop being socratic",
    r"no explanations?",
    r"no steps",
    r"no hints",
    r"jailbreak",
    r"modo solver",
    r"solver mode",
]

CODE_REQUEST_PATTERNS: list[str] = [
    r"(escreve|implementa|cria|faz|gera|programa|write|implement|create|make|generate|program|code)\b.*\b(c[óo]digo|fun[çc][ãa]o|programa|classe|m[ée]todo|script|function|class|method|code|solution|implementation|program)",
    r"(d[áa][\s-]?me|mostra[\s-]?me|partilha|give me|show me|share)\b.*\b(c[óo]digo|implementa[çc][ãa]o|solu[çc][ãa]o|code|implementation|solution|function|class|method|program|script)",
]

DIRECT_ANSWER_SIGNALS: list[str] = [
    r"a resposta [ée]",
    r"the answer is",
    r"a solu[çc][ãa]o [ée]",
    r"the solution is",
    r"o resultado [ée]",
    r"the result is",
    r"aqui est[áa] o c[óo]digo",
    r"here is the code",
    r"aqui est[áa] a (solu[çc][ãa]o|implementa[çc][ãa]o|resposta)",
    r"here is the (solution|implementation|answer)",
    r"aqui tens o c[óo]digo",
    r"here you have the code",
    r"aqui tens a (solu[çc][ãa]o|implementa[çc][ãa]o|resposta)",
    r"here you have the (solution|implementation|answer)",
    r"esta [ée] a resposta",
    r"this is the answer",
    r"esta [ée] a solu[çc][ãa]o",
    r"this is the solution",
    r"segue o c[óo]digo",
    r"below is the code",
    r"o erro est[áa] na palavra",
    r"the error is in the word",
    r"escrit[oa] incorretamente",
    r"incorretamente como",
    r"(is|are) (incorrectly|wrongly) (written|spelled)",
    r"is misspelled",
    r"devias? (usar|escrever|ser)",
    r"deverias? (usar|escrever)",
    r"should (use|write) ",
    r"troca .{1,30} por",
    r"substitui .{1,30} por",
    r"muda .{1,30} para",
    r"replace .{1,30} with",
    r"o correto (seria|[ée])",
    r"falta(-te)? (um|uma|o|a) ",
]

TUTOR_BENCHMARK_CRITERIA = ["faithfulness", "non_directiveness", "scaffolding", "clarity"]
