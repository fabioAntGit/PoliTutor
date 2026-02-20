"""
Utilities for extracting metadata from filenames.
"""

from pathlib import Path

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