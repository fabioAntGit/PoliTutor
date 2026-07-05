"""Build embedding chunks while preserving page and image provenance."""

import logging
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..shared.config import CHUNKING_STRATEGIES, CHUNK_SEPARATORS, CHUNK_MIN_LENGTH

logger = logging.getLogger(__name__)

_PAGE_MARKER_PATTERN = re.compile(r'\[PAGE:(\d+)\]')


def resolve_page_numbers(
    split: str,
    last_pages: list[int],
) -> tuple[list[int], list[int]]:
    """Return the pages covered by a raw split with [PAGE:N] markers."""
    found = [int(p) for p in _PAGE_MARKER_PATTERN.findall(split)]

    if not found:
        return last_pages, last_pages

    first_marker = _PAGE_MARKER_PATTERN.search(split)
    content_before_marker = split[:first_marker.start()].strip()

    if content_before_marker and last_pages:
        page_numbers = list(dict.fromkeys(
            last_pages + [p for p in found if p not in last_pages]
        ))
    else:
        page_numbers = list(dict.fromkeys(found))

    return page_numbers, [found[-1]]


def chunk_document(pages: list[dict]) -> list[dict]:
    """
    Split extracted pages into embedding chunks.

    Returns:
        Chunk dicts with text, image paths, and covered pages.
    """
    if not pages:
        return []

    source = pages[0]["metadata"].get("source", "default")
    base_metadata = pages[0]["metadata"]

    images_by_page = {
        page["metadata"]["page_number"]: page.get("image_paths", [])
        for page in pages
    }

    marked_parts = []
    for page in pages:
        text = page.get("text", "").strip()
        if text:
            marked_parts.append(f"[PAGE:{page['metadata']['page_number']}]\n{text}")
    marked_text = "\n\n".join(marked_parts)

    config = CHUNKING_STRATEGIES.get(source, CHUNKING_STRATEGIES["default"])
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        separators=CHUNK_SEPARATORS,
    )

    chunks: list[dict] = []
    seen_images: set[str] = set()
    last_pages: list[int] = []

    for split in splitter.split_text(marked_text):
        page_numbers, last_pages = resolve_page_numbers(split, last_pages)
        clean_text = _PAGE_MARKER_PATTERN.sub("", split).strip()

        if len(clean_text) <= CHUNK_MIN_LENGTH:
            continue

        chunk_images = []
        for p in page_numbers:
            for img_path in images_by_page.get(p, []):
                if img_path not in seen_images:
                    seen_images.add(img_path)
                    chunk_images.append(img_path)

        chunk_metadata = {k: v for k, v in base_metadata.items() if k != "page_number"}
        chunk_metadata["pages"] = page_numbers

        chunks.append({
            "text": clean_text,
            "image_paths": chunk_images,
            "metadata": chunk_metadata,
        })

    # Keep images from low-text pages by attaching them to the nearest chunk.
    all_chunk_pages = {p for chunk in chunks for p in chunk["metadata"]["pages"]}
    for page_num, img_paths in images_by_page.items():
        if page_num in all_chunk_pages or not img_paths:
            continue
        best_chunk = min(
            chunks,
            key=lambda c: min(abs(p - page_num) for p in c["metadata"]["pages"]),
        )
        for img_path in img_paths:
            if img_path not in seen_images:
                seen_images.add(img_path)
                best_chunk["image_paths"].append(img_path)
                logger.debug(
                    "Orphan image from page %d assigned to chunk covering pages %s.",
                    page_num, best_chunk["metadata"]["pages"],
                )

    logger.info("Created %d chunks for '%s'.", len(chunks), base_metadata.get("filename"))
    return chunks
