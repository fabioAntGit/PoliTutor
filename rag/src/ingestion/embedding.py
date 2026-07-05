"""Embedding and image-ingestion helpers."""

import base64
import logging
import os
import time

from ..shared.config import (
    IMAGE_API_DELAY,
    MAX_IMAGE_API_CALLS,
    OPENROUTER_MODEL_IMAGE_SUMMARIZATION,
)
from ..shared.prompts import IMAGE_EMBEDDING_PROMPT
from ..shared.call_model import OpenRouterClient
from ..shared.interfaces.vector_store import IVectorStore
from ..shared.chroma_vector_store import ChromaVectorStore
from ..shared.embedding import get_embedder
from ..shared.models import ImageSummary

logger = logging.getLogger(__name__)

_image_api_calls: int = 0


def build_meta(chunk: dict, doc_type: str, **extra) -> dict:
    """Build ChromaDB-safe metadata for a text or image chunk."""
    meta = chunk["metadata"].copy()
    if "pages" in meta:
        meta["pages"] = str(meta["pages"])
    meta["type"] = doc_type
    meta.update(extra)
    return meta


def embed_chunks(
    chunks: list[dict],
    file_stem: str,
    model_name: str | None = None,
    collection_name: str | None = None,
    store: IVectorStore | None = None,
) -> None:
    """Embed text chunks and relevant image summaries into the vector store."""
    valid_chunks = [c for c in chunks if c["text"].strip()]

    if not valid_chunks:
        logger.warning("No valid text found for '%s'. Skipping.", file_stem)
        return

    embedder = get_embedder(model_name)
    store = store or ChromaVectorStore(collection_name)

    texts, ids, metadatas = [], [], []

    for i, chunk in enumerate(valid_chunks):
        texts.append(chunk["text"])
        ids.append(f"{file_stem}_{i}")
        metadatas.append(build_meta(chunk, "text"))

        for j, image_path in enumerate(chunk.get("image_paths", [])):
            context = "\n".join(c["text"] for c in valid_chunks[i:i+3])
            result = image_resume(image_path, context)

            if result and result.relevant:
                texts.append(result.summary)
                ids.append(f"{file_stem}_img_{i}_{j}")
                metadatas.append(build_meta(chunk, "image", image_path=image_path))
            else:
                try:
                    os.remove(image_path)
                except OSError as e:
                    logger.warning("Failed to delete unused image '%s': %s", image_path, e)

    try:
        embeddings = embedder.embed_documents(texts)
        store.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        text_count = sum(1 for m in metadatas if m["type"] == "text")
        image_count = sum(1 for m in metadatas if m["type"] == "image")
        logger.info("Upserted %d text + %d image chunks for '%s'.", text_count, image_count, file_stem)

    except Exception as e:
        logger.error("Failed to upsert embeddings for '%s': %s", file_stem, e)
        raise


def image_resume(image_path: str, context: str) -> ImageSummary | None:
    """Summarize an image for embedding, or return None when skipped/failed."""
    global _image_api_calls

    if MAX_IMAGE_API_CALLS is not None and _image_api_calls >= MAX_IMAGE_API_CALLS:
        logger.info("Image API limit reached (%d/%d). Skipping '%s'.", _image_api_calls, MAX_IMAGE_API_CALLS, image_path)
        return None

    try:
        if IMAGE_API_DELAY > 0:
            time.sleep(IMAGE_API_DELAY)

        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
    except OSError as e:
        logger.error("Failed to read image '%s': %s", image_path, e)
        return None

    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": IMAGE_EMBEDDING_PROMPT.format(context=context)},
            {"type": "image", "base64": b64, "mime_type": "image/png"},
        ],
    }]

    _image_api_calls += 1
    return OpenRouterClient().call_structured(
        messages=messages,
        schema=ImageSummary,
        max_tokens=500,
        model=OPENROUTER_MODEL_IMAGE_SUMMARIZATION,
    )
