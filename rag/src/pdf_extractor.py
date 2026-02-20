"""
PDF Element Extraction and Transformation.
Converts raw PDF partitions into structured, cleaned page-based JSON data.
"""

import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any, Tuple

from unstructured.cleaners.core import clean, replace_unicode_quotes
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import convert_to_dict

from config import (
    PDF_PROCESSING_CONFIG,
    ELEMENT_TYPES_TO_EXCLUDE,
)
from utils import extract_metadata_from_filename

logger = logging.getLogger(__name__)

def extract_elements_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Partitions a PDF into structured elements using the Unstructured library.
    """
    logger.info(f"Starting partitioning for: {pdf_path}")
    elements = partition_pdf(filename=pdf_path, **PDF_PROCESSING_CONFIG)
    return convert_to_dict(elements)

def filter_elements(elements: List[Dict[str, Any]], keywords_to_exclude: List[str]) -> List[Dict[str, Any]]:
    """
    Filters elements by type and sanitizes text content by removing sensitive keywords.
    """
    if not keywords_to_exclude:
        return [el for el in elements if el.get("type") not in ELEMENT_TYPES_TO_EXCLUDE]

    # Pre-compile regex for faster keyword replacement
    pattern = re.compile("|".join(map(re.escape, keywords_to_exclude)), re.IGNORECASE)
    
    filtered = []
    for el in elements:
        if el.get("type") in ELEMENT_TYPES_TO_EXCLUDE:
            continue

        text_content = el.get("text") or ""
        if text_content:
            # Replace keywords with a single space " "
            el["text"] = pattern.sub(" ", text_content)
        
        filtered.append(el)
    return filtered

def build_page_content(page_elements: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    """
    Consolidates text elements and extracts base64 images from a single page.
    Tables are preserved as HTML for better LLM reasoning.
    """
    lines = []
    images_b64 = []

    for el in page_elements:
        el_type = el.get("type")

        # Handle Images
        if el_type == "Image":
            metadata = el.get("metadata") or {}
            b64 = metadata.get("image_base64")
            if b64:
                images_b64.append(b64)
                metadata["image_base64"] = None 
            continue

        # Handle Tables
        if el_type == "Table":
            metadata = el.get("metadata") or {}
            html = metadata.get("text_as_html") or metadata.get("html")
            if html:
                lines.append(html)
            else:
                txt = (el.get("text") or "").strip()
                if txt:
                    lines.append(f"<pre>{txt}</pre>")
            continue

        # Handle General Text
        txt = (el.get("text") or "").strip()
        if txt:
            txt = replace_unicode_quotes(txt)
            txt = clean(txt, extra_whitespace=True, bullets=True)
            lines.append(txt)

    return "\n\n".join(lines).strip(), images_b64

def group_elements_by_page(elements: List[Dict[str, Any]], source_filename: str) -> List[Dict[str, Any]]:
    """
    Groups filtered elements by page and attaches global document metadata.
    """
    pages = defaultdict(list)
    for el in elements:
        page_number = el.get("metadata", {}).get("page_number", 1)
        pages[page_number].append(el)

    # Extract metadata
    source_type, course_code = extract_metadata_from_filename(source_filename)

    grouped = []
    for page in sorted(pages.keys()):
        page_elements = pages[page]
        page_text, images = build_page_content(page_elements)

        if not page_text and not images:
            continue

        first_el_md = page_elements[0].get("metadata") or {} if page_elements else {}

        grouped.append({
            "metadata": {
                "filename": source_filename,
                "course": course_code,
                "source": source_type,
                "page_number": page,
                "filetype": first_el_md.get("filetype"),
            },
            "text": page_text,
            "images": images,
        })
    return grouped

def save_json(data: Any, output_path: str) -> None:
    """
    Saves the structured data to a JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)