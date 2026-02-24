from embedding import connect_chromadb
import pandas as pd
from renumics import spotlight
import numpy as np

def visualize():
    collection = connect_chromadb()
    
    results = collection.get(include=["documents", "embeddings", "metadatas"])
    
    df = pd.DataFrame({
        "id": results["ids"],
        "document": results["documents"],
        **{k: [m[k] for m in results["metadatas"]] for k in results["metadatas"][0].keys()}
    })
    df["embedding"] = [np.array(e) for e in results["embeddings"]]
    
    spotlight.show(df, embed=["embedding"])

if __name__ == "__main__":
    visualize()
