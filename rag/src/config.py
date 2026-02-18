"""
Configs para o processamento de PDFs
"""
import os
from pathlib import Path

# Caminhos e diretorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_PATH = os.getenv("RAW_DATA_PATH", os.path.normpath(os.path.join(BASE_DIR, "..", "data", "raw")))
COURSE_PATH = os.getenv("COURSE_PATH", os.path.join(RAW_DATA_PATH, "ED"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(RAW_DATA_PATH, "processed_json"))
OUTPUT_DIR_BEFORE = os.getenv("OUTPUT_DIR_BEFORE", os.path.join(RAW_DATA_PATH, "processedBefore_json"))

# Keywords para filtrar/excluir
KEYWORDS_TO_EXCLUDE = [
    "ESCOLA",
    "SUPERIOR",
    "DE TECNOLOGIA",
    "E GESTÃO",
]

# Configurações de processamento do PDF
PDF_PROCESSING_CONFIG = {
    "strategy": "hi_res",
    # "languages": ["por", "eng"],
    "infer_table_structure": True,
    "extract_image_block_types": ["Image", "Table"],
    "extract_images_in_pdf": True,
    "extract_image_block_to_payload": False,
    "chunking_strategy": None,
    "include_orig_elements": False,
}

# Tipos de elementos a filtrar
ELEMENT_TYPES_TO_EXCLUDE = [
    "Footer",
    "Header",
]

# Tipos de elementos a ignorar na construção do texto
ELEMENT_TYPES_TO_SKIP_IN_TEXT = [
    "Image",
    "Table",
]

# Tipos de source válidos
SOURCE_TYPE_MAPPING = {
    "apontamentos": "apontamentos",
    "slides": "slides",
}
DEFAULT_SOURCE_TYPE = "unknown"