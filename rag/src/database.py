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
    Initializes and returns a singleton connection to the ChromaDB Cloud cluster.
    
    Authenticates using the CHROMA_API_KEY, CHROMA_TENANT, and CHROMA_DATABASE 
    environment variables. The connection is maintained in memory for subsequent calls.

    Returns:
        chromadb.CloudClient: The established database client session.
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

def get_collection(name: str | None = None) -> chromadb.Collection:
    """
    Retrieves an existing ChromaDB collection or safely creates a new one.
    
    When creating a new collection, it automatically injects the exact HNSW 
    (Hierarchical Navigable Small World) index parameters defined in `config.py` 
    to ensure predictable search performance and latency.

    Args:
        name (str | None): The explicit name of the collection to target. 
                           Falls back to the default CHROMA_COLLECTION_NAME if None.

    Returns:
        chromadb.Collection: The active collection instance ready for upserts or queries.
    """
    client = get_client()
    collection_name = name or CHROMA_COLLECTION_NAME
    
    return client.get_or_create_collection(
        name=collection_name,
        metadata={
            "hnsw:space":           CHROMA_HNSW_SPACE,
            "hnsw:M":               CHROMA_HNSW_M,
            "hnsw:construction_ef": CHROMA_HNSW_CONSTRUCTION_EF,
            "hnsw:search_ef":       CHROMA_HNSW_SEARCH_EF,
        }
    )