"""
Embedding and Vector Database Service.
Handles vector generation and storage in ChromaDB Cloud.
"""

import os
import logging
from typing import List, Dict, Any, Optional

import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL, CHROMA_COLLECTION_NAME

logger = logging.getLogger(__name__)

# Cache the embedder instance to avoid reloading the model multiple times
_embedder: Optional[HuggingFaceEmbeddings] = None

def connect_chromadb() -> chromadb.Collection:
    """Connects to ChromaDB Cloud and returns the specified collection."""
    client = chromadb.CloudClient(
        api_key=os.getenv("CHROMA_API_KEY"),
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
    )
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",
            "hnsw:M": 32,
            "hnsw:construction_ef": 200,
            "hnsw:search_ef": 100,
        }
    )
    
    db_name = os.getenv('CHROMA_DATABASE')
    logger.info(f"Connected to ChromaDB Cloud | Database: {db_name}")
    return collection

def get_embedder() -> HuggingFaceEmbeddings:
    """
    Returns a singleton instance of the embedding model.
    Loads it only once per session.
    """
    global _embedder
    
    if _embedder is None:
        logger.info(f"Loading embedding model into memory: {EMBEDDING_MODEL}")
        _embedder = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    return _embedder

def embed_chunks(chunks: List[Dict[str, Any]], file_stem: str) -> None:
    """
    Generates embeddings and upserts chunks into ChromaDB.
    """
    valid_chunks = [c for c in chunks if c["text"].strip()]

    if not valid_chunks:
        logger.warning(f"No valid text found for '{file_stem}'. Skipping.")
        return

    embedder = get_embedder()
    collection = connect_chromadb()

    texts = [c["text"] for c in valid_chunks]

    # Unique IDs: filename + index
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
        logger.info(f"Successfully upserted {len(texts)} chunks for '{file_stem}'.")

    except Exception as e:
        logger.error(f"Failed to upsert embeddings for '{file_stem}': {e}")
        raise