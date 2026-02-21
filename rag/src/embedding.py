import os
import logging
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings

def connect_chromadb() -> chromadb.Collection:
    client = chromadb.CloudClient(
        api_key=os.getenv("CHROMA_API_KEY"),
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
    )
    collection = client.get_or_create_collection(name="PoliTutor-Docs")
    logging.info(f"Connected to ChromaDB Cloud (database: {os.getenv('CHROMA_DATABASE')})")
    return collection

def create_embedder(model_name: str = "Qwen/Qwen3-VL-Embedding-8B") -> HuggingFaceEmbeddings:
    logging.info(f"Loading embedding model: {model_name}")
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )