"""
Vector Database Service.

Manages the connection to ChromaDB Cloud and exposes a singleton client
and collection accessor.
"""

import logging
import os

import chromadb

from config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_HNSW_CONSTRUCTION_EF,
    CHROMA_HNSW_M,
    CHROMA_HNSW_SEARCH_EF,
    CHROMA_HNSW_SPACE,
)

logger = logging.getLogger(__name__)

_chroma_client: chromadb.CloudClient | None = None


def get_client() -> chromadb.CloudClient:
    """
    Returns the singleton ChromaDB Cloud client, initializing it on first call.

    Authenticates using the CHROMA_API_KEY, CHROMA_TENANT, and CHROMA_DATABASE
    environment variables. The connection is reused across all subsequent calls.

    Returns:
        The established ChromaDB Cloud client session.
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
    Retrieves or creates a ChromaDB collection with the configured HNSW index parameters.

    HNSW parameters (space, M, construction_ef, search_ef) are injected at creation
    time to ensure consistent search performance. If the collection already exists,
    the parameters are ignored by ChromaDB.

    Args:
        name: Collection name to target. Uses config default if None.

    Returns:
        The active collection instance, ready for upserts or queries.
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
        },
    )