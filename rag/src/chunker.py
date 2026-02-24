"""
Document Chunking Service.
Segments processed pages into embedding-ready chunks
"""

import logging
import re
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import CHUNKING_CONFIG_APONTAMENTOS, CHUNKING_CONFIG_SLIDES

logger = logging.getLogger(__name__)

def build_splitter(source: str) -> RecursiveCharacterTextSplitter:
    """
    Builds the text splitter. 
    Added punctuation marks to separators for better semantic boundaries.
    """
    config = CHUNKING_CONFIG_SLIDES if source == "slides" else CHUNKING_CONFIG_APONTAMENTOS

    return RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        separators=["```\n", "\n\n", "\n", ". ", "? ", "! ", " ", ""],
    )

def chunk_document(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    source = pages[0]["metadata"]["source"]
    splitter = build_splitter(source)
    
    # Guarda imagens por página
    images_by_page = {
        page["metadata"]["page_number"]: page.get("images", [])
        for page in pages
    }
    
    # Concatena todo o texto com marcadores de página
    parts = []
    for page in pages:
        text = page.get("text", "").strip()
        if text:
            parts.append(f"[PAGE:{page['metadata']['page_number']}]\n{text}")
    
    full_text = "\n\n".join(parts)
    splits = splitter.split_text(full_text)
    
    base_metadata = pages[0]["metadata"]
    last_pages = []
    chunks = []
    
    for i, split in enumerate(splits):
        page_numbers = [int(p) for p in re.findall(r'\[PAGE:(\d+)\]', split)]
        
        if page_numbers:
            last_pages = page_numbers
        else:
            page_numbers = last_pages
        
        clean_text = re.sub(r'\[PAGE:\d+\]\n?', '', split).strip()
        
        chunk_images = []
        for p in page_numbers:
            chunk_images.extend(images_by_page.get(p, []))
        
        chunks.append({
            "text": clean_text,
            "images": chunk_images,
            "metadata": {
                "filename": base_metadata["filename"],
                "course": base_metadata["course"],
                "source": base_metadata["source"],
                "filetype": base_metadata["filetype"],
                "pages": page_numbers,
            }
        })
    
    return chunks