"""
PDF Element Extraction and Transformation.
Converts raw PDF partitions into structured, cleaned page-based JSON data.
"""

import logging
import re
import os
from collections import defaultdict
from typing import List, Dict, Any, Tuple

from unstructured.cleaners.core import clean, replace_unicode_quotes
from unstructured.partition.api import partition_via_api
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
    elements = partition_via_api(
        filename=pdf_path,
        api_url=os.getenv("UNSTRUCTURED_API_URL"),
        api_key=os.getenv("UNSTRUCTURED_API_KEY"),
        **PDF_PROCESSING_CONFIG
    )
    return convert_to_dict(elements)

def filter_elements(elements: List[Dict[str, Any]], keywords_to_exclude: List[str]) -> List[Dict[str, Any]]:
    """
    Filters elements by type and sanitizes text content by removing sensitive keywords.
    """
    if not keywords_to_exclude:
        return [el for el in elements if el.get("type") not in ELEMENT_TYPES_TO_EXCLUDE]

    pattern = re.compile("|".join(map(re.escape, keywords_to_exclude)), re.IGNORECASE)
    
    filtered = []
    for el in elements:
        if el.get("type") in ELEMENT_TYPES_TO_EXCLUDE:
            continue

        text_content = el.get("text") or ""
        if text_content and pattern.search(text_content):
            el = {**el, "text": re.sub(r'\s+', ' ', pattern.sub("", text_content)).strip()}

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

        if el_type == "CodeSnippet":
            code = (el.get("text") or "").strip()
            if code:
                lines.append(f"```\n{code}\n```")
            continue

        # Handle General Text
        txt = (el.get("text") or "").strip()
        if txt:
            txt = replace_unicode_quotes(txt)
            txt = clean(txt, extra_whitespace=True, bullets=True)
            lines.append(txt)

    return "\n\n".join(lines).strip(), images_b64

def group_elements_by_page(elements: List[Dict[str, Any]], source_filename: str, source_type: str, course_code: str, ) -> List[Dict[str, Any]]:
    """
    Groups filtered elements by page and attaches global document metadata.
    """
    pages = defaultdict(list)
    for el in elements:
        page_number = el.get("metadata", {}).get("page_number", 1)
        pages[page_number].append(el)
        
    grouped = []
    for page in sorted(pages.keys()):
        page_elements = pages[page]
        page_text, images = build_page_content(page_elements)

        if not page_text and not images:
            continue

        first_el_md = page_elements[0].get("metadata") or {}

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