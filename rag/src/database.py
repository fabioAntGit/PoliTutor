"""
Vector Database Service.

Manages the connection to ChromaDB Cloud and exposes a singleton client
and collection accessor.
"""

import os
import logging
from typing import Any

import chromadb
from config import CHROMA_COLLECTION_NAME, CHROMA_HNSW_SPACE, CHROMA_HNSW_M, CHROMA_HNSW_CONSTRUCTION_EF, CHROMA_HNSW_SEARCH_EF

logger = logging.getLogger(__name__)

_chroma_client: Any = None

def get_client() -> chromadb.CloudClient:
    """
    Returns a singleton ChromaDB Cloud client.
    """
    global _chroma_client

    if _chroma_client is None:
        _chroma_client = chromadb.CloudClient(
            api_key=os.getenv("CHROMA_API_KEY"),
            tenant=os.getenv("CHROMA_TENANT"),
            database=os.getenv("CHROMA_DATABASE"),
        )
        logger.info("Connected to ChromaDB Cloud | Database: %s", os.getenv("CHROMA_DATABASE"))

    return _chroma_client

def get_collection() -> chromadb.Collection:
    """
    Returns the ChromaDB collection defined in config.

    Uses cosine similarity with HNSW indexing. The collection is created
    if it does not already exist.
    """
    client = get_client()

    return client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={
            "hnsw:space":           CHROMA_HNSW_SPACE,
            "hnsw:M":               CHROMA_HNSW_M,
            "hnsw:construction_ef": CHROMA_HNSW_CONSTRUCTION_EF,
            "hnsw:search_ef":       CHROMA_HNSW_SEARCH_EF,
        }
    )