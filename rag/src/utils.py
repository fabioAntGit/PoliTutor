"""
Utilities for extracting metadata from filenames and file paths.
"""
import os
from config import SOURCE_TYPE_MAPPING, DEFAULT_SOURCE_TYPE

def extract_course_from_filename(filename: str) -> str:
    """
    Extracts the course code from the filename.
    Assumes the format: <year>.<course>.<rest>.pdf
    Example: "2024.ED.Aula01.pdf" -> "ED"
    Returns an empty string if the format is not recognised.
    """
    stem = os.path.splitext(filename)[0]
    parts = stem.split(".")
    return parts[1] if len(parts) > 1 else ""

def extract_source_type(pdf_path: str) -> str:
    """
    Determines the source type based on the folder names in the PDF path.
    Example: ".../slides/file.pdf" -> "slides"
    Returns DEFAULT_SOURCE_TYPE if no known folder is found.
    """
    parts = pdf_path.lower().split(os.sep)
    for source_key, source_value in SOURCE_TYPE_MAPPING.items():
        if source_key in parts:
            return source_value
    return DEFAULT_SOURCE_TYPE