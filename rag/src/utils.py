"""
Utilities for file management and metadata extraction.
"""

import json
import logging
from pathlib import Path
from typing import Any
from config import VALID_SOURCE_TYPES

logger = logging.getLogger(__name__)

def save_json(data: Any, output_path: str | Path) -> None:
    """
    Serializes data to JSON and saves it to the specified path.
    Creates parent directories automatically.
    """
    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to save JSON to {path}: {str(e)}")
        raise

def extract_metadata_from_filename(filename: str) -> tuple[str, str]:
    """
    Extracts source_type and course_code from a PDF filename.

    Expected format: <source_type>.<course_code>.<description>.pdf
    Example: "Apontamentos.ED.CAP1.pdf" -> ("apontamentos", "ed")

    The source_type is validated against VALID_SOURCE_TYPES (defined in config.py).
    The course_code must contain only alphanumeric characters.

    Args:
        filename: The PDF filename to parse (e.g. "Slides.ED.CAP1.pdf").

    Returns:
        A tuple (source_type, course_code), both normalized to lowercase.

    Raises:
        ValueError: If the filename has fewer than 2 dot-separated parts,
                    or if the course_code contains invalid characters.

    Warns:
        If source_type is not present in VALID_SOURCE_TYPES, a warning is
        logged but processing continues to avoid blocking unknown types.
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

    if not re.match(r'^[a-z0-9]+$', course_code):
        raise ValueError(
            f"course_code '{course_code}' in '{filename}' contains invalid characters."
        )

    return source_type, course_code