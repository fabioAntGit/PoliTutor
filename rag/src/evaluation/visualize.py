"""Renumics Spotlight visualization for ChromaDB embeddings."""

import argparse
import logging

import numpy as np
import pandas as pd
from renumics import spotlight

from ..shared.chroma_vector_store import get_collection

logger = logging.getLogger(__name__)


def visualize(collection_name: str | None = None) -> None:
    """Load a ChromaDB collection and open it in Spotlight."""
    collection = get_collection(collection_name)

    results = collection.get(include=["documents", "embeddings", "metadatas"])

    if not results.get("ids"):
        logger.warning("The collection '%s' is empty. Nothing to visualize.", collection.name)
        return

    df = pd.DataFrame({
        "id": results["ids"],
        "document": results["documents"],
    })

    if results.get("metadatas"):
        df_meta = pd.DataFrame(results["metadatas"])
        df = pd.concat([df, df_meta], axis=1)

    if results.get("embeddings") is not None:
        df["embedding"] = [np.array(e) for e in results["embeddings"]]

    logger.info("Displaying %d documents in Spotlight.", len(df))
    spotlight.show(df, embed=["embedding"])


if __name__ == "__main__":
    from ..shared.logging_config import setup_logging

    setup_logging()

    parser = argparse.ArgumentParser(description="ChromaDB Spotlight Visualizer")
    parser.add_argument("--collection", type=str, help="Specific ChromaDB collection to visualize")
    args = parser.parse_args()

    visualize(args.collection)
