"""
Embedding Service.

Handles the loading of the HuggingFace embedding model and the generation
and upsert of embeddings into ChromaDB via the database module.
"""

import logging
from typing import List, Dict, Any

from langchain_huggingface import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL
from database import get_collection

logger = logging.getLogger(__name__)

_embedder: HuggingFaceEmbeddings | None = None

def get_embedder() -> HuggingFaceEmbeddings:
    """
    Returns a singleton instance of the HuggingFace embedding model.
    """
    global _embedder
    
    if _embedder is None:
        logger.info("Loading embedding model into memory: %s", EMBEDDING_MODEL)
        _embedder = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    return _embedder

def embed_chunks(chunks: List[Dict[str, Any]], file_stem: str) -> None:
    """
    Generates embeddings and upserts chunks into ChromaDB.
    """
    valid_chunks = [c for c in chunks if c["text"].strip()]

    if not valid_chunks:
        logger.warning("No valid text found for '%s'. Skipping.", file_stem)
        return

    embedder = get_embedder()
    collection = get_collection()

    texts = [c["text"] for c in valid_chunks]
    ids = [f"{file_stem}_{i}" for i in range(len(valid_chunks))]

    metadatas = []
    for chunk in valid_chunks:
        meta = chunk["metadata"].copy()

        if "pages" in meta:
            meta["pages"] = str(meta["pages"])

        meta["model_name"] = EMBEDDING_MODEL
        metadatas.append(meta)

    try:
        embeddings = embedder.embed_documents(texts)

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Successfully upserted %d chunks for '%s'.", len(texts), file_stem)

    except Exception as e:
        logger.error("Failed to upsert embeddings for '%s': %s", file_stem, e)
        raise