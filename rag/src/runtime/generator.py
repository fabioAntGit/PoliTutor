"""
Tutor Generation Module.

Takes the retrieved chunks from ChromaDB and a student query, builds a
grounded context prompt, and calls OpenRouter (OPENROUTER_MODEL_GENERATOR) to
generate a Socratic tutoring response in Portuguese.

The tutor never gives direct answers or ready-made code — it guides the
student via questions and scaffolding.
"""

import json
import logging
import re

from ..shared.config import OPENROUTER_MODEL_GENERATOR, TUTOR_API_ERROR_MESSAGE, TUTOR_FALLBACK_MESSAGE, TUTOR_SYSTEM_PROMPT


from ..shared.call_model import OpenRouterClient
from ..shared.interfaces.model_client import IModelClient
from ..shared.models import RetrievalResults
from contracts.rag.models import TutorResponse, TutorSource

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

def build_messages(
    system_content: str,
    summary: str,
    history: list[dict],
    query: str,
) -> list[dict]:
    """Assembles the message list for the LLM."""
    messages: list[dict] = [{"role": "system", "content": system_content}]

    if summary:
        messages.append({"role": "assistant", "content": f"Resumo: {summary}"})

    for turn in history:
        role = turn.get("role")
        content = turn.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": query})
    return messages


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
        sources.append(TutorSource(filename=filename, pages=pages))
    return sources

def generate(
    query: str,
    results: RetrievalResults,
    summary: str = "",
    history: list[dict] | None = None,
    is_retrieval_fallback: bool = False,
    memory: str = "",
    model_client: IModelClient | None = None,
) -> TutorResponse:
    history = history or []
    model_client = model_client or OpenRouterClient()

    if results.is_empty():
        logger.info("[GENERATE] No RAG chunks — continuing dialogue from conversation context.")
        context = ""
        sources = []
    else:
        context = build_context(results)
        sources = build_sources(results)

    system_content = TUTOR_SYSTEM_PROMPT.format(
        student_memory=memory,
        rag_context=context,
    )
    messages = build_messages(system_content, summary, history, query)

    raw_answer = model_client.call(
        messages=messages,
        max_tokens=2000,
        model=OPENROUTER_MODEL_GENERATOR,
        response_format={"type": "json_object"},
    )

    if raw_answer is None:
        logger.error("[GENERATE] API ERROR: OpenRouter returned no answer")
        return TutorResponse(
            answer=TUTOR_API_ERROR_MESSAGE,
            sources=[],
            is_fallback=True,
            is_retrieval_fallback=is_retrieval_fallback,
        )

    logger.debug("[GENERATE] Raw LLM response (first 500 chars):\n%s", raw_answer[:500])

    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_answer.strip())
    try:
        data = json.loads(clean)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("[GENERATE] LLM response is not valid JSON (%s) — using raw text.", exc)
        return TutorResponse(
            answer=raw_answer,
            sources=sources,
            is_fallback=False,
            is_retrieval_fallback=is_retrieval_fallback,
        )

    if data.get("is_fallback", False):
        logger.warning("[GENERATE] FALLBACK REASON: LLM set is_fallback=true.")
        return TutorResponse(
            answer=TUTOR_FALLBACK_MESSAGE,
            sources=[],
            is_fallback=True,
            is_retrieval_fallback=is_retrieval_fallback,
        )

    answer = data.get("answer", "")
    if not answer:
        logger.warning("[GENERATE] FALLBACK REASON: LLM returned empty answer string.")
        return TutorResponse(
            answer=TUTOR_FALLBACK_MESSAGE,
            sources=[],
            is_fallback=True,
            is_retrieval_fallback=is_retrieval_fallback,
        )

    llm_sources = [
        TutorSource(filename=s.get("filename", ""), pages=s.get("pages", []))
        for s in data.get("sources", [])
        if s.get("filename")
    ]

    logger.info("Tutor response generated from %d source chunks.", len(llm_sources))
    return TutorResponse(
        answer=answer,
        sources=llm_sources,
        is_fallback=False,
        is_retrieval_fallback=is_retrieval_fallback,
    )
