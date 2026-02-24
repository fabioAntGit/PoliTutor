import os
import json
import logging
import chromadb
from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from config import OUTPUT_DIR_CHUNKS, EMBEDDING_MODEL

def connect_chromadb() -> chromadb.Collection:
    client = chromadb.CloudClient(
        api_key=os.getenv("CHROMA_API_KEY"),
        tenant=os.getenv("CHROMA_TENANT"),
        database=os.getenv("CHROMA_DATABASE"),
    )
    collection = client.get_or_create_collection(name="PoliTutor-Docs")
    logging.info(f"Connected to ChromaDB Cloud (database: {os.getenv('CHROMA_DATABASE')})")
    return collection

def create_embedder(model_name: str = EMBEDDING_MODEL) -> HuggingFaceEmbeddings:
    logging.info(f"Loading embedding model: {model_name}")
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

# TODO: Quando ja nao estivermos em fase de testes, ja nao será preciso ler os json files, mas sim receber diretamente os chunks da pipeline
def embed_from_chunks():
    chunk_files = list(Path(OUTPUT_DIR_CHUNKS).glob("*_chunks.json"))
    if not chunk_files:
        logging.warning("No chunked JSON files found.")
        return

    embedder = create_embedder()
    collection = connect_chromadb()

    for file_path in chunk_files:
        logging.info(f"Processing: {file_path.name}")
        chunks = json.loads(file_path.read_text(encoding="utf-8"))

        texts = [chunk["text"] for chunk in chunks if chunk["text"].strip()]
        ids = [f"{file_path.stem}_{i}" for i, chunk in enumerate(chunks) if chunk["text"].strip()]
        metadatas = []
        for chunk in chunks:
            if not chunk["text"].strip():
                continue
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
        logging.info(f"{file_path.name}: {len(texts)} chunks embedded")

    logging.info("Done.")
