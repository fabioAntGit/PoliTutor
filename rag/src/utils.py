"""
Utilities for file management and metadata extraction.
"""

import json
import logging
from pathlib import Path
from typing import Any

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
    Extracts source_type and course_code from the filename.
    
    Expected format: <source_type>.<course_code>.<description>.pdf
    Example: "Apontamentos.ED.CAP1.pdf" -> ("apontamentos", "ed")
    
    Returns:
        tuple: (source_type, course_code) in lowercase. 
               Returns ("unknown", "unknown") if format is invalid.
    """
    stem = Path(filename).stem
    parts = stem.split(".")

    if len(parts) >= 2:
        source_type = parts[0].lower()
        course_code = parts[1].lower()
        return source_type, course_code

    return "unknown", "unknown"