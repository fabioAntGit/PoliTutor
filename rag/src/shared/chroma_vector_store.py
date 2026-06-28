"""ChromaDB Cloud vector store and client."""

import logging

import os
import chromadb
from chromadb.api import ClientAPI

from .config import CHROMA_COLLECTION_NAME, CHROMA_METADATA
from .interfaces.vector_store import IVectorStore
from .models import RetrievalResults

logger = logging.getLogger(__name__)

_chroma_client: ClientAPI | None = None

class ChromaVectorStore(IVectorStore):
    def __init__(self, collection_name: str | None = None) -> None:
        self._collection_name = collection_name
        self._collection = None 

    @property
    def _coll(self):
        if self._collection is None:
            self._collection = get_collection(self._collection_name)
        return self._collection

    def search(self, course: str, query_vector: list[float], top_k: int) -> RetrievalResults:
        raw = self._coll.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where={"course": course.strip().lower()},
        )
        return RetrievalResults.from_chroma_dict(raw)

    def upsert(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        self._coll.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def exists(self, filename: str) -> bool:
        existing = self._coll.get(where={"filename": filename}, limit=1)
        return bool(existing and existing.get("ids"))

def get_client() -> ClientAPI:
    global _chroma_client

    if _chroma_client is None:
        _chroma_client = chromadb.CloudClient(
            api_key=os.environ["CHROMA_API_KEY"],
            tenant=os.environ["CHROMA_TENANT"],
            database=os.environ["CHROMA_DATABASE"],
        )
        logger.info("Connected to ChromaDB Cloud | Database: %s", os.environ["CHROMA_DATABASE"])

    return _chroma_client


def get_collection(name: str | None = None) -> chromadb.Collection:
    client = get_client()
    collection_name = name or CHROMA_COLLECTION_NAME

    return client.get_or_create_collection(
        name=collection_name,
        metadata=CHROMA_METADATA
    )
