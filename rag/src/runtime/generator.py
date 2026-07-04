"""Socratic tutor response generation."""

import json
import logging

from ..shared.config import OPENROUTER_MODEL_GENERATOR, TUTOR_API_ERROR_MESSAGE, TUTOR_FALLBACK_MESSAGE, TUTOR_SYSTEM_PROMPT, TUTOR_TEMPERATURE


from ..shared.call_model import OpenRouterClient
from ..shared.interfaces.model_client import IModelClient
from ..shared.models import GeneratorOutput, RetrievalResults
from contracts.rag.models import TutorResponse, TutorSource

logger = logging.getLogger(__name__)


def build_context(results: RetrievalResults) -> str:
    """Format retrieved chunks as numbered prompt context."""
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


def generate(
    query: str,
    results: RetrievalResults,
    summary: str = "",
    history: list[dict] | None = None,
    is_retrieval_fallback: bool = False,
    memory: str = "",
    course_scope: str = "",
    model_client: IModelClient | None = None,
) -> TutorResponse:
    """Generate the final tutor answer and fallback flags."""
    history = history or []
    model_client = model_client or OpenRouterClient()

    if results.is_empty():
        logger.info("[GENERATE] No RAG chunks — continuing dialogue from conversation context.")
        context = ""
    else:
        context = build_context(results)

    system_content = TUTOR_SYSTEM_PROMPT.format(
        student_memory=memory,
        rag_context=context,
        course_scope=course_scope,
    )
    messages = build_messages(system_content, summary, history, query)

    data = model_client.call_structured(
        messages=messages,
        schema=GeneratorOutput,
        temperature=TUTOR_TEMPERATURE,
        model=OPENROUTER_MODEL_GENERATOR,
    )

    if data is None:
        logger.error("[GENERATE] API ERROR: OpenRouter returned no answer")
        return TutorResponse(
            answer=TUTOR_API_ERROR_MESSAGE,
            sources=[],
            is_fallback=True,
            is_retrieval_fallback=is_retrieval_fallback,
        )

    if data.is_fallback:
        logger.warning("[GENERATE] FALLBACK REASON: LLM set is_fallback=true.")
        return TutorResponse(
            answer=TUTOR_FALLBACK_MESSAGE,
            sources=[],
            is_fallback=True,
            is_retrieval_fallback=is_retrieval_fallback,
        )

    if not data.answer:
        logger.warning("[GENERATE] FALLBACK REASON: LLM returned empty answer string.")
        return TutorResponse(
            answer=TUTOR_FALLBACK_MESSAGE,
            sources=[],
            is_fallback=True,
            is_retrieval_fallback=is_retrieval_fallback,
        )

    llm_sources = [s for s in data.sources if s.filename]

    logger.info("Tutor response generated from %d source chunks.", len(llm_sources))
    return TutorResponse(
        answer=data.answer,
        sources=llm_sources,
        is_fallback=False,
        is_retrieval_fallback=is_retrieval_fallback,
    )
