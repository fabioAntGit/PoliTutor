"""
Configuration settings
"""
import os

# Paths and directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_PATH = os.getenv("RAW_DATA_PATH", os.path.normpath(os.path.join(BASE_DIR, "..", "data", "raw")))
COURSE_PATH = os.getenv("COURSE_PATH", os.path.join(RAW_DATA_PATH, "ED"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(RAW_DATA_PATH, "processed_json"))
OUTPUT_DIR_BEFORE = os.getenv("OUTPUT_DIR_BEFORE", os.path.join(RAW_DATA_PATH, "processedBefore_json"))

# Keywords used to exclude elements whose text contains them
KEYWORDS_TO_EXCLUDE = [
    "ESCOLA",
    "SUPERIOR",
    "DE TECNOLOGIA",
    "E GESTÃO",
]

# Settings passed directly to unstructured's partition_pdf
PDF_PROCESSING_CONFIG = {
    "strategy": "hi_res",
    "infer_table_structure": True,
    "extract_image_block_types": ["Image", "Table"],
    "extract_images_in_pdf": True,
    "extract_image_block_to_payload": False,
    "chunking_strategy": None,
    "include_orig_elements": False,
}

# Element types removed before any processing (e.g. headers/footers)
ELEMENT_TYPES_TO_EXCLUDE = [
    "Footer",
    "Header",
]

# Element types ignored when building the final page text
# Tables are included inline as HTML; images are discarded
ELEMENT_TYPES_TO_SKIP_IN_TEXT = [
    "Image",
]

# Mapping between folder name and source type
SOURCE_TYPE_MAPPING = {
    "apontamentos": "apontamentos",
    "slides": "slides",
}
DEFAULT_SOURCE_TYPE = "unknown"