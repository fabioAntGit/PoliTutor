"""
Document Chunking Service.
Segments processed pages into embedding-ready chunks
"""

import logging
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNKING_CONFIG

logger = logging.getLogger(__name__)

def build_splitter() -> RecursiveCharacterTextSplitter:
    """
    Builds the text splitter. 
    Added punctuation marks to separators for better semantic boundaries.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNKING_CONFIG["chunk_size"],
        chunk_overlap=CHUNKING_CONFIG["chunk_overlap"],
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
    )

def chunk_page(page: Dict[str, Any], splitter: RecursiveCharacterTextSplitter) -> List[Dict[str, Any]]:
    """
    Chunks a single page while preserving multimodal context.
    Images are attached only to the first chunk to avoid duplication.
    """
    text = page.get("text", "").strip()
    images = page.get("images", [])
    metadata = page.get("metadata", {})

    if not text and not images:
        return []

    splits = splitter.split_text(text) if text else [""]
    total_splits = len(splits)

    return [
        {
            "text": split,
            "images": images if i == 0 else [],
            "metadata": {**metadata, "chunk_index": i, "total_chunks": total_splits},
        }
        for i, split in enumerate(splits)
    ]

def chunk_document(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Orchestrates the chunking of all document pages.
    """
    splitter = build_splitter()
    all_chunks = []
    
    for page in pages:
        all_chunks.extend(chunk_page(page, splitter))
        
    return all_chunks