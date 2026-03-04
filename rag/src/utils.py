"""
File management and metadata extraction utilities.

This module provides functions to parse and validate filenames following 
the internal convention: <source_type>.<course_code>.<description>.[pdf,pptx,md...].
"""

import re
import logging
from pathlib import Path
from config import VALID_SOURCE_TYPES

logger = logging.getLogger(__name__)

COURSE_CODE_PATTERN = re.compile(r'^[a-z]+$')

def extract_metadata_from_filename(filename: str) -> tuple[str, str]:
    """
    Extracts source_type and course_code from a filename.

    Expected format: <source_type>.<course_code>.<description>.[pdf,pptx,md...]
    Example: "Slides.ED.CAP1.[pdf,pptx,md...]" -> ("slides", "ed")
    """
    stem = Path(filename).stem
    parts = stem.split(".")

    if len(parts) < 2:
        raise ValueError(
            f"Filename '{filename}' does not follow the expected format "
            f"'<source_type>.<course_code>.<description>.[pdf,pptx,md...]'."
        )

    source_type = parts[0].lower()
    course_code = parts[1].lower()

    if source_type not in VALID_SOURCE_TYPES:
        logger.warning(
            "Unknown source_type '%s' in '%s'. Expected one of: %s.",
            source_type, filename, VALID_SOURCE_TYPES
        )

    if not COURSE_CODE_PATTERN.match(course_code):
        raise ValueError(
            f"course_code '{course_code}' in '{filename}' contains invalid characters."
        )

    return source_type, course_code