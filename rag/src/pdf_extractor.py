import os
import json
from collections import defaultdict
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import convert_to_dict
from config import (
    PDF_PROCESSING_CONFIG,
    ELEMENT_TYPES_TO_EXCLUDE,
    ELEMENT_TYPES_TO_SKIP_IN_TEXT,
)
from utils import extract_course_from_filename

def extract_elements_from_pdf(pdf_path: str):
    elements = partition_pdf(filename=pdf_path, **PDF_PROCESSING_CONFIG)
    return convert_to_dict(elements)

def filter_elements(elements: list, keywords_to_exclude: list) -> list:
    filtered = []
    for el in elements:
        if el.get("type") in ELEMENT_TYPES_TO_EXCLUDE:
            continue
        text_content = el.get("text") or ""
        if any(key.lower() in text_content.lower() for key in keywords_to_exclude):
            continue
        filtered.append(el)
    return filtered

def build_page_text(page_elements: list) -> str:
    lines = []
    for el in page_elements:
        if el.get("type") in ELEMENT_TYPES_TO_SKIP_IN_TEXT:
            continue
        txt = (el.get("text") or "").strip()
        if txt:
            lines.append(txt)
    page_text = "\n".join(lines)
    while "\n\n\n" in page_text:
        page_text = page_text.replace("\n\n\n", "\n\n")
    return page_text.strip()

def extract_tables_html(page_elements: list) -> list:
    tables = []
    for el in page_elements:
        if el.get("type") != "Table":
            continue
        md = el.get("metadata") or {}
        html = md.get("text_as_html") or md.get("html")
        if not html:
            txt = (el.get("text") or "").strip()
            if txt:
                html = f"<pre>{txt}</pre>"
        if html:
            tables.append(html)
    return tables

def group_elements_by_page(elements: list, source_filename=None, source_type=None) -> list:
    pages = defaultdict(list)
    for el in elements:
        page_number = el.get("metadata", {}).get("page_number", -1)
        pages[page_number].append(el)

    course_code = extract_course_from_filename(source_filename or "")

    grouped = []
    for page in sorted(pages.keys()):
        page_elements = pages[page]
        base_md = page_elements[0].get("metadata") or {} if page_elements else {}

        page_text = build_page_text(page_elements)
        tables = extract_tables_html(page_elements)

        if not page_text and not tables:
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
            "tables": tables,
        })
    return grouped

def save_json(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)