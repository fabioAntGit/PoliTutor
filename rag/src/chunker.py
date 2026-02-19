"""
Chunking of extracted per-page JSON into embedding-ready chunks.
Prepares data in the format expected by Qwen3-VL-Embedding-8B
"""
import os
import json
import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNKING_CONFIG, OUTPUT_DIR_CHUNKS

def build_splitter() -> RecursiveCharacterTextSplitter:
    """
    Builds the LangChain text splitter based on CHUNKING_CONFIG.
    Separators are ordered to prefer splitting on paragraph breaks
    before falling back to line breaks or spaces.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNKING_CONFIG["chunk_size"],
        chunk_overlap=CHUNKING_CONFIG["chunk_overlap"],
        separators=["\n\n", "\n", " "],
    )


def chunk_page(page: dict, splitter: RecursiveCharacterTextSplitter) -> list[dict]:
    """
    Chunks a single page into one or more embedding-ready objects.
    Pages short enough to fit in a single chunk are kept as-is.
    Each chunk carries the original page metadata plus a chunk_index.
    Images are only attached to the first chunk to avoid duplicating heavy base64 data.
    """
    text = page.get("text", "").strip()
    images = page.get("images", [])
    metadata = page.get("metadata", {})

    if not text and not images:
        return []

    if len(text) <= CHUNKING_CONFIG["chunk_size"]:
        chunk = {
            "text": text,
            "metadata": {**metadata, "chunk_index": 0, "total_chunks": 1},
        }
        if images:
            chunk["images"] = images
        return [chunk]

    splits = splitter.split_text(text) if text else []
    chunks = []
    for i, split in enumerate(splits):
        if len(split.strip()) < CHUNKING_CONFIG["min_chunk_length"]:
            continue
        chunk = {
            "text": split,
            "metadata": {**metadata, "chunk_index": i, "total_chunks": len(splits)},
        }
        # Images are only attached to the first chunk of the page (REVIEW THIS DECISION)
        if i == 0 and images:
            chunk["images"] = images
        chunks.append(chunk)
    return chunks


def chunk_document(pages: list[dict]) -> list[dict]:
    """
    Applies chunking to all pages of a document.
    Returns a flat list of all chunks across all pages.
    """
    splitter = build_splitter()
    chunks = []
    for page in pages:
        chunks.extend(chunk_page(page, splitter))
    return chunks


def save_chunks(chunks: list[dict], output_path: str) -> None:
    """
    Saves the list of chunks to a JSON file,
    creating intermediate directories if needed.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=4, ensure_ascii=False)