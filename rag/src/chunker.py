"""
Document Chunking Service.
Segments processed pages into embedding-ready chunks while preserving page context.
"""

import logging
import re
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNKING_STRATEGIES

logger = logging.getLogger(__name__)

def build_splitter(source: str) -> RecursiveCharacterTextSplitter:
    """
    Builds the text splitter based on the source type configuration.
    Falls back to 'default' if the source type is not explicitly configured.
    """
    config = CHUNKING_STRATEGIES.get(source, CHUNKING_STRATEGIES["default"])

    logger.debug(f"Building splitter for source '{source}' with config: {config}")

    return RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        separators=["```\n", "\n\n", "\n", ". ", "? ", "! ", " ", ""],
    )

def chunk_document(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes a list of pages into chunks, maintaining image associations 
    and tracking page numbers across splits.
    """
    if not pages:
        return []

    source = pages[0]["metadata"].get("source", "default")
    splitter = build_splitter(source)
    
    # Map images to their respective page numbers
    images_by_page = {
        page["metadata"]["page_number"]: page.get("images", [])
        for page in pages
    }
    
    # Concatenate text with page markers to track source pages after splitting
    parts = []
    for page in pages:
        text = page.get("text", "").strip()
        if text:
            page_num = page['metadata']['page_number']
            parts.append(f"[PAGE:{page_num}]\n{text}")
    
    full_text = "\n\n".join(parts)
    splits = splitter.split_text(full_text)
    
    base_metadata = pages[0]["metadata"]
    last_pages = []
    chunks = []

    # Regex pattern to find page markers
    page_marker_pattern = re.compile(r'\[PAGE:(\d+)\]')
    
    for split in splits:
        # Extract all page numbers present in this chunk
        page_numbers = [int(p) for p in page_marker_pattern.findall(split)]
        
        # If no marker is found, the chunk belongs to the previous page(s)
        if page_numbers:
            last_pages = page_numbers
        else:
            page_numbers = last_pages
        
        # Clean the markers from the final text
        clean_text = page_marker_pattern.sub('', split).strip()
        
        # Collect images from all pages involved in this chunk
        chunk_images = []
        for p in page_numbers:
            chunk_images.extend(images_by_page.get(p, []))

        chunk_metadata = base_metadata.copy()

        keys_to_remove = ["page_number"]
        
        for key in keys_to_remove:
            chunk_metadata.pop(key, None)

        chunk_metadata["pages"] = page_numbers    

        chunks.append({
            "text": clean_text,
            "images": chunk_images,
            "metadata": chunk_metadata
        })
    
    logger.info(f"Created {len(chunks)} chunks for {base_metadata.get('filename')}")
    return chunks