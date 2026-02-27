"""
Visualization utility for ChromaDB embeddings using Renumics Spotlight.
"""

import logging
import pandas as pd
import numpy as np
from renumics import spotlight
from database import get_collection

logger = logging.getLogger(__name__)

def visualize():
    """
    Fetches data from ChromaDB and launches the Spotlight UI.
    """
    collection = get_collection()
    
    results = collection.get(include=["documents", "embeddings", "metadatas"])    

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
    visualize()