"""
Tutor Generation Module.

Takes the retrieved chunks from ChromaDB and a student query, builds a
grounded context prompt, and calls the IAEdu API (GPT-4o) to generate a
Socratic tutoring response in Portuguese.

The tutor never gives direct answers or ready-made code — it guides the
student through questions and hints based exclusively on the course material.
"""

import json
import logging

from config import TUTOR_FALLBACK_MESSAGE, TUTOR_SYSTEM_PROMPT
from iaedu import call_iaedu
from models import RetrievalResults, TutorResponse, TutorSource

logger = logging.getLogger(__name__)

def build_context(results: RetrievalResults) -> str:
    """
    Formats retrieved chunks into a numbered context string for the LLM prompt.

    Each entry includes the source filename, page numbers, and chunk text,
    giving the model full attribution information alongside the content.

    Args:
        results: The ranked retrieval results to format.

    Returns:
        A multi-line string with all chunks numbered and labelled by source.
    """
    parts = []
    for i, (doc, meta) in enumerate(zip(results.documents, results.metadatas), start=1):
        filename = meta.get("filename", "Desconhecido")
        pages_raw = meta.get("pages", "[]")
        pages = json.loads(pages_raw) if isinstance(pages_raw, str) else pages_raw
        pages_str = ", ".join(str(p) for p in pages) if pages else "?"
        parts.append(f"[{i}] {filename} — p.{pages_str}\n{doc.strip()}")
    return "\n\n".join(parts)

def build_sources(results: RetrievalResults) -> list[TutorSource]:
    """
    Converts retrieval metadata into a list of TutorSource objects.

    Args:
        results: The ranked retrieval results.

    Returns:
        A list of TutorSource instances, one per chunk.
    """
    sources = []
    for meta, score in zip(results.metadatas, results.scores):
        filename = meta.get("filename", "Desconhecido")
        pages_raw = meta.get("pages", "[]")
        pages = json.loads(pages_raw) if isinstance(pages_raw, str) else pages_raw
        sources.append(TutorSource(filename=filename, pages=pages, score=float(score)))
    return sources

def generate(query: str, results: RetrievalResults) -> TutorResponse:
    """
    Generates a Socratic tutoring response grounded in the retrieved course material.

    If no relevant chunks were retrieved, returns a fallback TutorResponse without
    calling the API. Otherwise, builds a context prompt and calls the IAEdu API.
    On API failure, also returns the fallback response.

    Args:
        query:   The student's question.
        results: Ranked chunks retrieved from ChromaDB.

    Returns:
        A TutorResponse with the tutor's answer, cited sources, and fallback flag.
    """
    if results.is_empty():
        logger.warning("No retrieval results — returning fallback response.")
        return TutorResponse(answer=TUTOR_FALLBACK_MESSAGE, sources=[], is_fallback=True)

    context = build_context(results)
    sources = build_sources(results)

    prompt = (
        f"{TUTOR_SYSTEM_PROMPT}\n\n"
        f"Contexto dos materiais da UC:\n{context}\n\n"
        f"Pergunta do aluno:\n{query}"
    )

    answer = call_iaedu(prompt)

    if answer is None:
        logger.error("IAEdu API returned no answer — returning fallback response.")
        return TutorResponse(answer=TUTOR_FALLBACK_MESSAGE, sources=sources, is_fallback=True)

    logger.info("Tutor response generated from %d source chunks.", len(sources))
    return TutorResponse(answer=answer, sources=sources, is_fallback=False)