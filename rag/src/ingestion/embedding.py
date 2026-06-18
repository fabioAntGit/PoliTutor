"""
Embedding Service.

Handles the loading of the HuggingFace embedding model and the generation
and upsert of embeddings into ChromaDB via the database module.
Supports multiple embedding models and collections for benchmarking.
"""

import base64
import json
import logging
import os
import re
import requests
import time

from ..shared.config import (
    IMAGE_API_DELAY,
    IMAGE_EMBEDDING_PROMPT,
    MAX_IMAGE_API_CALLS,
    OPENROUTER_MODEL_IMAGE_SUMMARIZATION,
)
from ..shared.database import get_collection
from ..shared.embedding import get_embedder

logger = logging.getLogger(__name__)

_image_api_calls: int = 0


def build_meta(chunk: dict, doc_type: str, **extra) -> dict:
    """
    Builds a ChromaDB-compatible metadata dict from a chunk.

    Converts the 'pages' list to a string, since ChromaDB metadata values
    must be scalar types. The 'type' field distinguishes text from image chunks.

    Args:
        chunk:    Chunk dict with a 'metadata' key.
        doc_type: Either 'text' or 'image'.
        **extra:  Additional key-value pairs merged into the metadata
                  (e.g. image_path for image chunks).

    Returns:
        Flat metadata dict safe for ChromaDB upsert.
    """
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
) -> None:
    """
    Generates embeddings for text chunks and relevant images, then upserts
    everything into ChromaDB in a single batch call.

    For each chunk's images, calls image_resume() to classify and summarize
    them via OpenRouter. Only relevant images (relevant=True) are embedded.
    Text chunk IDs follow the pattern '{file_stem}_{i}'; image IDs use
    '{file_stem}_img_{i}_{j}'.

    Args:
        chunks:          List of chunk dicts with 'text', 'image_paths', and 'metadata'.
        file_stem:       Source file identifier used as the ID prefix.
        model_name:      HuggingFace embedding model. Uses config default if None.
        collection_name: ChromaDB collection name. Uses config default if None.
    """
    valid_chunks = [c for c in chunks if c["text"].strip()]

    if not valid_chunks:
        logger.warning("No valid text found for '%s'. Skipping.", file_stem)
        return

    embedder = get_embedder(model_name)
    collection = get_collection(collection_name)

    texts, ids, metadatas = [], [], []

    for i, chunk in enumerate(valid_chunks):
        texts.append(chunk["text"])
        ids.append(f"{file_stem}_{i}")
        metadatas.append(build_meta(chunk, "text"))

        for j, image_path in enumerate(chunk.get("image_paths", [])):
            context = "\n".join(c["text"] for c in valid_chunks[i:i+3])
            result = image_resume(image_path, context)

            if result and result.get("relevant"):
                texts.append(result.get("summary", ""))
                ids.append(f"{file_stem}_img_{i}_{j}")
                metadatas.append(build_meta(chunk, "image", image_path=image_path))

    try:
        embeddings = embedder.embed_documents(texts)
        collection.upsert(
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


def image_resume(image_path: str, context: str) -> dict | None:
    """
    Classifies and summarizes an image via the OpenRouter API.

    Sends the image as base64 alongside surrounding chunk text as context.
    The model is expected to return JSON with 'relevant' (bool) and 'summary' (str).
    Irrelevant images (logos, decorative elements) return relevant=False.

    Retries up to 3 times with exponential backoff on HTTP 429 (rate limit).
    Respects MAX_IMAGE_API_CALLS to cap total API usage per pipeline run.

    Args:
        image_path: Absolute path to the PNG image on disk.
        context:    Surrounding chunk text sent as context to the model.

    Returns:
        Dict with 'relevant' (bool) and 'summary' (str), or None on failure
        or if the API call limit has been reached.
    """
    global _image_api_calls

    if MAX_IMAGE_API_CALLS is not None and _image_api_calls >= MAX_IMAGE_API_CALLS:
        logger.info("Image API limit reached (%d/%d). Skipping '%s'.", _image_api_calls, MAX_IMAGE_API_CALLS, image_path)
        return None

    try:
        if IMAGE_API_DELAY > 0:
            time.sleep(IMAGE_API_DELAY)

        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('OPENROUTER_KEY')}"},
                json={
                    "model": OPENROUTER_MODEL_IMAGE_SUMMARIZATION,
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": IMAGE_EMBEDDING_PROMPT.format(context=context)},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                        ],
                    }],
                    "max_tokens": 500,
                    "temperature": 0.2,
                },
                timeout=(10, 180),
            )

            if response.status_code == 429:
                logger.warning("Rate limited (429) for '%s'. Retrying in %ds (Attempt %d/%d)...", image_path, retry_delay, attempt + 1, max_retries)
                time.sleep(retry_delay)
                retry_delay *= 2
                continue

            _image_api_calls += 1

            if not response.ok:
                logger.warning("OpenRouter returned %d for '%s': %s", response.status_code, image_path, response.text[:200])
                return None

            content = response.json()["choices"][0]["message"]["content"]
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
            return json.loads(content)

        logger.error("Max retries reached for '%s' due to rate limiting.", image_path)
        return None

    except Exception as e:
        logger.error("Image API error for '%s': %s", image_path, e)
        return None
