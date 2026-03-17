"""
ChromaDB Embeddings Visualization Tool using Renumics Spotlight to visually
inspect, filter, and analyze the document chunks and their high-dimensional
embeddings stored in the ChromaDB cloud instance. It helps identifying clusters
of similar documents and debugging embedding quality.
"""

import argparse
import logging

import numpy as np
import pandas as pd
from renumics import spotlight

from database import get_collection

logger = logging.getLogger(__name__)


def visualize(collection_name: str | None = None) -> None:
    """
    Fetches embedding data from ChromaDB and launches the Spotlight UI.

    Args:
        collection_name: The specific ChromaDB collection to load.
            If None, the default collection defined in config is used.
    """
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
    parser = argparse.ArgumentParser(description="ChromaDB Spotlight Visualizer")
    parser.add_argument("--collection", type=str, help="Specific ChromaDB collection to visualize")
    args = parser.parse_args()

    visualize(args.collection)
