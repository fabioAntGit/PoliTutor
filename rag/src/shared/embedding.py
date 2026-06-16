import logging

from langchain_huggingface import HuggingFaceEmbeddings

from .config import EMBEDDING_DEVICE, EMBEDDING_MODEL, EMBEDDING_NORMALIZE

logger = logging.getLogger(__name__)

_embedder_cache: dict[str, HuggingFaceEmbeddings] = {}


def get_embedder(model_name: str | None = None) -> HuggingFaceEmbeddings:
    model_name = model_name or EMBEDDING_MODEL
    if model_name not in _embedder_cache:
        logger.info("Loading embedding model into memory: %s", model_name)
        _embedder_cache[model_name] = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": EMBEDDING_NORMALIZE},
        )
    return _embedder_cache[model_name]
