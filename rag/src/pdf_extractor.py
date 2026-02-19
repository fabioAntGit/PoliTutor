"""
Extraction and transformation of PDF elements into page-structured JSON.
"""
import os
import json
from collections import defaultdict
from unstructured.cleaners.core import clean, replace_unicode_quotes
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import convert_to_dict
from config import (
    PDF_PROCESSING_CONFIG,
    ELEMENT_TYPES_TO_EXCLUDE,
    ELEMENT_TYPES_TO_SKIP_IN_TEXT,
)
from utils import extract_course_from_filename

def extract_elements_from_pdf(pdf_path: str) -> list:
    """
    Runs partition_pdf on the given file and returns the elements as a list of dicts.
    """
    elements = partition_pdf(filename=pdf_path, **PDF_PROCESSING_CONFIG)
    return convert_to_dict(elements)

def filter_elements(elements: list, keywords_to_exclude: list) -> list:
    """
    Removes elements whose type is in ELEMENT_TYPES_TO_EXCLUDE
    or whose text contains any of the keywords to exclude.
    """
    filtered = []
    for el in elements:
        if el.get("type") in ELEMENT_TYPES_TO_EXCLUDE:
            continue
        text_content = el.get("text") or ""
        if any(keyword.lower() in text_content.lower() for keyword in keywords_to_exclude):
            continue
        filtered.append(el)
    return filtered

def build_page_content(page_elements: list) -> tuple[str, list[str]]:
    """
    Builds the text and image list for a page preserving the original element order.
    Tables are represented inline as HTML.
    Images are returned as a list of base64 strings, extracted from the payload.
    """
    lines = []
    images_b64 = []

    for el in page_elements:
        el_type = el.get("type")

        if el_type == "Image":
            md = el.get("metadata") or {}
            b64 = md.get("image_base64")
            if b64:
                images_b64.append(b64)
            continue

        if el_type == "Table":
            md = el.get("metadata") or {}
            html = md.get("text_as_html") or md.get("html")
            if html:
                lines.append(html)
            else:
                txt = (el.get("text") or "").strip()
                if txt:
                    lines.append(f"<pre>{txt}</pre>")
        else:
            txt = (el.get("text") or "").strip()
            if len(txt) >= 3:
                txt = replace_unicode_quotes(txt)
                txt = clean(txt, extra_whitespace=True, bullets=True)
                lines.append(txt)

    return "\n\n".join(lines).strip(), images_b64

def group_elements_by_page(elements: list, source_filename: str = None, source_type: str = None) -> list:
    """
    Groups elements by page number and builds one object per page
    containing metadata and text (with tables inline).
    Pages with no content are skipped.
    """
    pages = defaultdict(list)
    for el in elements:
        page_number = el.get("metadata", {}).get("page_number", -1)
        pages[page_number].append(el)

    course_code = extract_course_from_filename(source_filename or "")

    grouped = []
    for page in sorted(pages.keys()):
        page_elements = pages[page]
        base_md = page_elements[0].get("metadata") or {} if page_elements else {}
        page_text, images = build_page_content(page_elements)

        if not page_text and not images:
            continue

        grouped.append({
            "metadata": {
                "filename": source_filename,
                "course": course_code,
                "source": source_type,
                "page_number": page,
                "filetype": base_md.get("filetype"),
            },
            "text": page_text,
            "images": images,
        })
    return grouped

def save_json(data: object, output_path: str) -> None:
    """
    Serializes `data` to JSON and writes it to the given path,
    creating any intermediate directories if needed.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)