"""
Utilities for extracting metadata from filenames and file paths.
"""

from pathlib import Path
from config import SOURCE_TYPE_MAPPING, DEFAULT_SOURCE_TYPE

def extract_course_from_filename(filename: str) -> str:
    """
    Extracts the course code from the filename.
    
    Expected format: <year>.<course_code>.<description>.pdf
    Example: "2024.ED.Lesson01.pdf" -> "ED"
    
    Args:
        filename (str): The name of the file including extension.
        
    Returns:
        str: The course code if the format matches, otherwise an empty string.
    """
    parts = Path(filename).stem.split(".")

    if len(parts) >= 2:
        return parts[1]

    return ""

def extract_source_type(pdf_path: str) -> str:
    """
    Determines the source category (e.g., slides, exams) based on the directory names.
        
    Args:
        pdf_path (str): The full or relative path to the PDF file.
        
    Returns:
        str: The mapped source type or DEFAULT_SOURCE_TYPE if no match is found.
    """
    path_obj = Path(pdf_path)
    path_components = [part.lower() for part in path_obj.parts]
    
    for source_key, source_value in SOURCE_TYPE_MAPPING.items():
        if source_key.lower() in path_components:
            return source_value
            
    return DEFAULT_SOURCE_TYPE