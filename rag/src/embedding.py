"""
Embedding Service.

Handles the loading of the HuggingFace embedding model and the generation
and upsert of embeddings into ChromaDB via the database module.
"""

import json
import re
import base64
import logging
import os
import requests
import time
from config import EMBEDDING_MODEL, IMAGE_EMBEDDING_PROMPT, OPENROUTER_MODEL, MAX_IMAGE_API_CALLS, EMBEDDING_DEVICE, EMBEDDING_NORMALIZE, IMAGE_API_DELAY
from typing import List, Dict, Any

from langchain_huggingface import HuggingFaceEmbeddings
from database import get_collection

logger = logging.getLogger(__name__)

_embedder_cache: dict[str, HuggingFaceEmbeddings] = {}
_image_api_calls = 0

def get_embedder_for_model(model_name: str) -> HuggingFaceEmbeddings:
    """
    Returns a cached HuggingFace embedder for the given model name.
    Loads the model on first use.
    """
    if model_name not in _embedder_cache:
        logger.info("Loading embedding model into memory: %s", model_name)
        _embedder_cache[model_name] = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": EMBEDDING_NORMALIZE},
        )
    return _embedder_cache[model_name]

def get_embedder() -> HuggingFaceEmbeddings:
    """Returns the default embedder defined in config."""
    return get_embedder_for_model(EMBEDDING_MODEL)

def _build_meta(chunk: Dict[str, Any], doc_type: str, **extra) -> Dict[str, Any]:
    """Builds a metadata dict from a chunk, converting pages to str."""
    meta = chunk["metadata"].copy()
    if "pages" in meta:
        meta["pages"] = str(meta["pages"])
    meta["type"] = doc_type
    meta.update(extra)
    return meta


def embed_chunks(chunks: List[Dict[str, Any]], file_stem: str) -> None:
    """
    Generates embeddings and upserts chunks into ChromaDB.
    For chunks with images, sends them to the LLM for classification/summarization
    and creates separate image embeddings.
    """
    valid_chunks = [c for c in chunks if c["text"].strip()]

    if not valid_chunks:
        logger.warning("No valid text found for '%s'. Skipping.", file_stem)
        return

    embedder = get_embedder()
    collection = get_collection()

    texts, ids, metadatas = [], [], []

    text_idx = 0
    for i, chunk in enumerate(valid_chunks):
        # --- Text chunk ---
        texts.append(chunk["text"])
        ids.append(f"{file_stem}_{text_idx}")
        metadatas.append(_build_meta(chunk, "text"))
        text_idx += 1

        # --- Image chunks ---
        for j, image_path in enumerate(chunk.get("image_paths", [])):
            context = "\n".join(c["text"] for c in valid_chunks[i:i+3])
            result = image_resume(image_path, context)

            if result and result.get("relevant"):
                texts.append(result.get("summary", ""))
                ids.append(f"{file_stem}_img_{i}_{j}")
                metadatas.append(_build_meta(chunk, "image", image_path=image_path))

    try:
        embeddings = embedder.embed_documents(texts)

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        logger.info("Successfully upserted %d chunks for '%s'.", len(texts), file_stem)

        text_count = sum(1 for m in metadatas if m["type"] == "text")
        image_count = sum(1 for m in metadatas if m["type"] == "image")
        logger.info("Upserted %d text + %d image chunks for '%s'.", text_count, image_count, file_stem)

    except Exception as e:
        logger.error("Failed to upsert embeddings for '%s': %s", file_stem, e)
        raise

def image_resume(image_path: str, context: str) -> dict | None:
    """
    Sends an image to OpenRouter for classification and summarization.
    Returns dict with 'relevant' and 'summary' keys, or None on failure.
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
                    "model": OPENROUTER_MODEL,
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

            result = json.loads(content)
            return result
        
        logger.error("Max retries reached for '%s' due to rate limiting.", image_path)
        return None

    except Exception as e:
        logger.error("Image API error for '%s': %s", image_path, e)
        return None
