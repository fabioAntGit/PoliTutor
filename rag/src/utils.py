"""
File management and metadata extraction utilities.

This module provides functions to parse and validate PDF filenames following 
the internal convention: <source_type>.<course_code>.<description>.pdf.
"""

import re
import logging
import base64
from pathlib import Path
from config import VALID_SOURCE_TYPES
from config import IMAGES_OUTPUT_DIR

logger = logging.getLogger(__name__)

COURSE_CODE_PATTERN = re.compile(r'^[a-z]+$')

def extract_metadata_from_filename(filename: str) -> tuple[str, str]:
    """
    Extracts source_type and course_code from a PDF filename.

    Expected format: <source_type>.<course_code>.<description>.pdf
    Example: "Slides.ED.CAP1.pdf" -> ("slides", "ed")
    """
    stem = Path(filename).stem
    parts = stem.split(".")

    if len(parts) < 2:
        raise ValueError(
            f"Filename '{filename}' does not follow the expected format "
            f"'<source_type>.<course_code>.<description>.pdf'."
        )

    source_type = parts[0].lower()
    course_code = parts[1].lower()

    if source_type not in VALID_SOURCE_TYPES:
        logger.warning(
            f"Unknown source_type '{source_type}' in '{filename}'. "
            f"Expected one of: {VALID_SOURCE_TYPES}."
        )

    if not COURSE_CODE_PATTERN.match(course_code):
        raise ValueError(
            f"course_code '{course_code}' in '{filename}' contains invalid characters."
        )

    return source_type, course_code

def save_image(image_b64: str, source_filename: str, page_num: int, img_index: int) -> str:
    """Saves a base64 image to disk and returns its path."""
    try:
        source_type, course_code = extract_metadata_from_filename(source_filename)
    except ValueError:
        course_code = "unknown"
        source_type = "unknown"

    image_dir = IMAGES_OUTPUT_DIR / course_code / source_type / source_filename.replace(".pdf", "")
    image_dir.mkdir(parents=True, exist_ok=True)

    image_path = image_dir / f"p{page_num}_img{img_index}.png"
    with open(image_path, "wb") as f:
        f.write(base64.b64decode(image_b64))

    return str(image_path)