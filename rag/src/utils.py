import os
from config import SOURCE_TYPE_MAPPING, DEFAULT_SOURCE_TYPE

def extract_course_from_filename(filename: str) -> str:
    """
    Extrai o código do curso a partir do nome do ficheiro.
    Ex: "2024.ED.Aula01.pdf" -> "ED"
    """
    stem = os.path.splitext(filename)[0]
    parts = stem.split(".")
    return parts[1] if len(parts) > 1 else ""

def extract_source_type(pdf_path: str) -> str:
    """
    Determina o tipo de source com base na pasta em que o PDF se encontra.
    """
    parts = pdf_path.lower().split(os.sep)
    for source_key, source_value in SOURCE_TYPE_MAPPING.items():
        if source_key in parts:
            return source_value
    return DEFAULT_SOURCE_TYPE