import os
import logging
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from config import EMBEDDING_MODEL, CHROMA_COLLECTION_NAME

def connect_chromadb() -> chromadb.Collection:
    client = chromadb.CloudClient(
        api_key=os.getenv("CHROMA_API_KEY"),
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
    )
    collection = client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
    logging.info(f"Connected to ChromaDB Cloud (database: {os.getenv('CHROMA_DATABASE')})")
    return collection

def create_embedder(model_name: str = EMBEDDING_MODEL) -> HuggingFaceEmbeddings:
    logging.info(f"Loading embedding model: {model_name}")
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

def embed_chunks(chunks: list, file_stem: str) -> None:
    valid_chunks = [c for c in chunks if c["text"].strip()]
    if not valid_chunks:
        logging.warning(f"No valid chunks to embed for '{file_stem}'.")
        return

    embedder = create_embedder()
    collection = connect_chromadb()

    texts = [c["text"] for c in valid_chunks]
    ids = [f"{file_stem}_{i}" for i in range(len(valid_chunks))]
    metadatas = []
    for chunk in valid_chunks:
        meta = chunk["metadata"].copy()
        meta["pages"] = str(meta["pages"])
        meta["model_name"] = EMBEDDING_MODEL
        metadatas.append(meta)

    embeddings = embedder.embed_documents(texts)
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    logging.info(f"'{file_stem}': {len(texts)} chunks embedded.")