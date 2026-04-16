"""
Document Element Extraction and Transformation.

Converts raw document files into structured, cleaned, page-based data using
the Unstructured API. Handles text, tables, code snippets, and images, and
groups the resulting elements into a consistent page-centric format ready
for the chunking stage.
"""

import hashlib
import logging
import re
import os
from collections import defaultdict

from unstructured.cleaners.core import clean, replace_unicode_quotes
from unstructured.partition.api import partition_via_api
from unstructured.staging.base import convert_to_dict
from .utils import save_image

from .config import (
    FILE_PROCESSING_CONFIG,
    ELEMENT_TYPES_TO_EXCLUDE,
)

logger = logging.getLogger(__name__)


def extract_elements_from_file(file_path: str) -> list[dict]:
    """
    Partitions a document into structured elements via the Unstructured API.

    Uses the configuration defined in FILE_PROCESSING_CONFIG (hi-res strategy,
    table inference, image extraction). The result is converted to a list of
    plain dicts for downstream processing.

    Args:
        file_path: Absolute path to the document file (.pdf, .pptx, .md).

    Returns:
        List of element dicts, each with 'type', 'text', and 'metadata' keys.

    Raises:
        Exception: Re-raises any API or partitioning error after logging it.
    """
    logger.info("Sending file to Unstructured API: %s", file_path)
    try:
        elements = partition_via_api(
            filename=file_path,
            api_url=os.getenv("UNSTRUCTURED_API_URL"),
            api_key=os.getenv("UNSTRUCTURED_API_KEY"),
            **FILE_PROCESSING_CONFIG,
        )
        return convert_to_dict(elements)
    except Exception as e:
        logger.error("API partitioning failed for '%s': %s", file_path, e)
        raise


def filter_elements(
    elements: list[dict],
    keywords_to_exclude: list[str],
) -> list[dict]:
    """
    Removes unwanted elements and sanitizes text content.

    Two-pass filter:
        1. Drops elements whose type is in ELEMENT_TYPES_TO_EXCLUDE
           (e.g. Footer, Header, FigureCaption, UncategorizedText).
        2. For remaining elements, removes any noise keywords (e.g. author names,
           institutional headers) and collapses the resulting extra whitespace.

    Args:
        elements:           List of element dicts from extract_elements_from_file.
        keywords_to_exclude: Substrings to strip from element text.

    Returns:
        Filtered and sanitized list of element dicts.
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


def build_page_content(page_elements: list[dict]) -> tuple[str, list[str]]:
    """
    Consolidates a page's elements into a single text block and a list of images.

    Element types are handled as follows:
        - Image:       Base64 data is collected separately; no text is added.
        - Table:       Preserved as HTML if available, otherwise wrapped in
                       [TABLE DATA]...[END TABLE] markers.
        - CodeSnippet: Wrapped in markdown code fences (``` ... ```).
        - Other text:  Unicode quotes normalized, extra whitespace removed.

    Args:
        page_elements: List of element dicts belonging to a single page.

    Returns:
        A tuple of (page_text, images_b64) where page_text is the consolidated
        text and images_b64 is a list of base64-encoded image strings.
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


def group_elements_by_page(
    elements: list[dict],
    source_filename: str,
    source_type: str,
    course_code: str,
    skip_pages: int = 0,
    save_images: bool = False,
) -> list[dict]:
    """
    Groups extracted elements into a page-centric structure with consistent metadata.

    Pages are processed in ascending order. Cover or title pages can be skipped via
    skip_pages. Empty pages (no text and no images) are discarded.

    Args:
        elements:        List of element dicts from filter_elements.
        source_filename: Original document filename (e.g. 'Apontamentos.ED.CAP1.pdf').
        source_type:     Document source type (e.g. 'apontamentos', 'slides').
        course_code:     Course identifier (e.g. 'ed', 'pp').
        skip_pages:      Number of leading pages to skip (default 0).
        save_images:     If True, saves extracted images to disk and returns their paths.

    Returns:
        List of page dicts, each with:
            - 'metadata': filename, course, source, page_number, filetype.
            - 'text':     Consolidated page text.
            - 'image_paths': Paths to saved images (empty list if save_images=False).
    """
    pages_map: dict[int, list] = defaultdict(list)
    for el in elements:
        page_num = int(el.get("metadata", {}).get("page_number", 1))
        pages_map[page_num].append(el)

    grouped_data = []
    seen_images: set[str] = set()

    for page_num in sorted(pages_map.keys()):
        if skip_pages and page_num <= skip_pages:
            continue

        page_elements = pages_map[page_num]
        page_text, images_b64 = build_page_content(page_elements)

        if not page_text and not images_b64:
            continue

        image_paths = []
        if save_images:
            for idx, b64 in enumerate(images_b64):
                img_hash = hashlib.md5(b64.encode()).hexdigest()
                if img_hash in seen_images:
                    continue
                seen_images.add(img_hash)
                image_paths.append(save_image(b64, source_filename, page_num, idx))

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
            "image_paths": image_paths,
        })

    logger.info("Grouped %d pages for '%s'.", len(grouped_data), source_filename)
    return grouped_data
