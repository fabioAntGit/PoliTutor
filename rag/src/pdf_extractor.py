"""
PDF Element Extraction and Transformation.
Converts raw PDF partitions into structured, cleaned page-based data.
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

logger = logging.getLogger(__name__)

def extract_elements_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Partitions a PDF into structured elements via Unstructured API.
    """
    logger.info(f"Sending PDF to Unstructured API: {pdf_path}")

    try:
        elements = partition_via_api(
            filename=pdf_path,
            api_url=os.getenv("UNSTRUCTURED_API_URL"),
            api_key=os.getenv("UNSTRUCTURED_API_KEY"),
            **PDF_PROCESSING_CONFIG
        )
        return convert_to_dict(elements)
    except Exception as e:
        logger.error(f"API Partitioning failed for {pdf_path}: {e}")
        raise

def filter_elements(elements: List[Dict[str, Any]], keywords_to_exclude: List[str]) -> List[Dict[str, Any]]:
    """
    Filters elements by type and sanitizes text content by removing sensitive keywords.
    """
    elements = [el for el in elements if el.get("type") not in ELEMENT_TYPES_TO_EXCLUDE]

    if not keywords_to_exclude:
        return elements

    pattern = re.compile("|".join(map(re.escape, keywords_to_exclude)), re.IGNORECASE)
    
    for el in elements:
        text_content = el.get("text")
        if text_content and pattern.search(text_content):
            cleaned_text = pattern.sub("", text_content)
            el["text"] = re.sub(r'\s+', ' ', cleaned_text).strip()

    return elements

def build_page_content(page_elements: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
    """
    Consolidates text elements and extracts images. 
    Maintains semantic markers for tables and code.
    """
    lines = []
    images_b64 = []

    for el in page_elements:
        el_type = el.get("type")
        metadata = el.get("metadata") or {}

        if el_type == "Image":
            if b64 := metadata.get("image_base64"):
                images_b64.append(b64)
            continue

        if el_type == "Table":
            html = metadata.get("text_as_html") or metadata.get("html")
            lines.append(html if html else f"\n[TABLE DATA]\n{el.get('text', '')}\n[END TABLE]\n")
            continue

        if el_type == "CodeSnippet":
            if code := el.get("text", "").strip():
                lines.append(f"```\n{code}\n```")
            continue

        if txt := el.get("text", "").strip():
            txt = replace_unicode_quotes(txt)
            txt = clean(txt, extra_whitespace=True, bullets=True)
            lines.append(txt)

    return "\n\n".join(lines).strip(), images_b64

def group_elements_by_page(elements: List[Dict[str, Any]], source_filename: str, source_type: str, course_code: str, skip_pages: int = 0,) -> List[Dict[str, Any]]:
    """
    Groups elements into a page-centric structure with consistent metadata.
    """
    pages_map = defaultdict(list)
    for el in elements:
        page_num = int(el.get("metadata", {}).get("page_number", 1))
        pages_map[page_num].append(el)

    grouped_data = []
    for page_num in sorted(pages_map.keys()):
        if skip_pages and page_num <= skip_pages:
            continue
        page_elements = pages_map[page_num]
        page_text, images = build_page_content(page_elements)

        if not page_text and not images:
            continue

        filetype = page_elements[0].get("metadata", {}).get("filetype")

        grouped_data.append({
            "metadata": {
                "filename": source_filename,
                "course": course_code,
                "source": source_type,
                "page_number": page_num,
                "filetype": filetype,
            },
            "text": page_text,
            "images": images,
        })

    logger.info(f"Grouped {len(grouped_data)} pages for {source_filename}")
    return grouped_data