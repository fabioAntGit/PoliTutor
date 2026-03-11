"""
Shared Data Models.

Defines the core data structures used to pass information safely and 
consistently between different components of the RAG pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class RetrievalResults:
    """
    Encapsulates the results from a ChromaDB query and subsequent RAG operations.
    Provides a structured, type-safe alternative to nested dictionary unpacking.
    """
    ids: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    metadatas: List[Dict[str, Any]] = field(default_factory=list)
    distances: List[float] = field(default_factory=list)
    scores: List[float] = field(default_factory=list)

    @classmethod
    def from_chroma_dict(cls, results: Dict[str, Any]) -> "RetrievalResults":
        """
        Converts the raw ChromaDB output dictionary into structured RetrievalResults.
        Automatically calculates a normalized score from the HNSW distance if missing.
        """
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        
        scores = results.get("scores", [[]])[0]
        if not scores and distances:
            scores = [1.0 - d for d in distances]
            
        return cls(
            ids=list(ids) if ids else [],
            documents=list(results.get("documents", [[]])[0]),
            metadatas=list(results.get("metadatas", [[]])[0]),
            distances=list(distances) if distances else [],
            scores=list(scores) if scores else []
        )

    def is_empty(self) -> bool:
        """Checks if the result set is empty."""
        return len(self.ids) == 0