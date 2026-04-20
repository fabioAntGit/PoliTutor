"""
Tutor Generation Module.

Takes the retrieved chunks from ChromaDB and a student query, builds a
grounded context prompt, and calls the configured LLM backend to generate a
Socratic tutoring response in Portuguese.

The tutor never gives direct answers or ready-made code — it guides the
student through questions and hints based exclusively on the course material.

Backends (GENERATOR_BACKEND in config):
    - "iaedu"      — IAEdu streaming API (GPT-4o via institutional endpoint)
    - "openrouter" — OpenRouter API using OPENROUTER_MODEL_GENERATOR
"""

import json
import logging
import re

from config import GENERATOR_BACKEND, OPENROUTER_MODEL_GENERATOR, SOCRATIC_REDIRECT, TUTOR_FALLBACK_MESSAGE, TUTOR_SYSTEM_PROMPT

from guardrails import detect_direct_answer
from call_model import call_iaedu, call_openrouter
from models import IaEduCredentials, RetrievalResults, TutorResponse, TutorSource

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
        sources.append(TutorSource(filename=filename, pages=pages))
    return sources

def generate(
    query: str,
    results: RetrievalResults,
    iaedu_creds: IaEduCredentials | None = None,
) -> TutorResponse:
    """
    Generates a Socratic tutoring response grounded in the retrieved course material.

    If no relevant chunks were retrieved, returns a fallback TutorResponse without
    calling the LLM. Otherwise, builds a context prompt and calls the configured
    backend (GENERATOR_BACKEND). On API failure, also returns the fallback response.

    Args:
        query:        The student's question.
        results:      Ranked chunks retrieved from ChromaDB.
        iaedu_creds:  Per-request IAEdu credentials forwarded from the student's
                      frontend session. Required when GENERATOR_BACKEND == "iaedu".
                      If None, call_iaedu falls back to environment variables.

    Returns:
        A TutorResponse with the tutor's answer, cited sources, and fallback flag.
    """
    if results.is_empty():
        logger.warning("[GENERATE] FALLBACK REASON: No retrieval results (0 chunks).")
        return TutorResponse(answer=TUTOR_FALLBACK_MESSAGE, sources=[], is_fallback=True)

    context = build_context(results)
    sources = build_sources(results)

    prompt = TUTOR_SYSTEM_PROMPT.format(user_question=query, rag_context=context)

    if GENERATOR_BACKEND == "openrouter":
        raw_answer = call_openrouter(prompt, max_tokens=2000, temperature=0.3, model=OPENROUTER_MODEL_GENERATOR)
    else:
        creds = iaedu_creds.__dict__ if iaedu_creds else {}
        raw_answer = call_iaedu(prompt, **creds)

    if raw_answer is None:
        logger.error("[GENERATE] FALLBACK REASON: %s API returned no answer", GENERATOR_BACKEND)
        return TutorResponse(answer=TUTOR_FALLBACK_MESSAGE, sources=sources, is_fallback=True)

    logger.debug("[GENERATE] Raw LLM response (first 500 chars):\n%s", raw_answer[:500])

    # Parse the JSON response from the LLM
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_answer.strip())
    try:
        data = json.loads(clean)
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("[GENERATE] LLM response is not valid JSON (%s) — using raw text.", exc)
        return TutorResponse(answer=raw_answer, sources=sources, is_fallback=False)

    # Handle the case where the LLM itself decided the context is not relevant
    if data.get("is_fallback", False):
        logger.warning("[GENERATE] FALLBACK REASON: LLM set is_fallback=true.")
        return TutorResponse(answer=TUTOR_FALLBACK_MESSAGE, sources=[], is_fallback=True)

    answer = data.get("answer", "")
    if not answer:
        logger.warning("[GENERATE] FALLBACK REASON: LLM returned empty answer string.")
        return TutorResponse(answer=TUTOR_FALLBACK_MESSAGE, sources=[], is_fallback=True)

    # Use sources from LLM response (only the ones it actually cited)
    llm_sources = [
        TutorSource(filename=s.get("filename", ""), pages=s.get("pages", []))
        for s in data.get("sources", [])
        if s.get("filename")
    ]

    # Output guardrail: verify the response is Socratic
    if detect_direct_answer(answer):
        logger.warning("[GENERATE] Output guardrail triggered — replacing with Socratic redirect.")
        return TutorResponse(answer=SOCRATIC_REDIRECT, sources=llm_sources, is_fallback=False, is_output_guardrail=True)

    logger.info("Tutor response generated from %d source chunks.", len(llm_sources))
    return TutorResponse(answer=answer, sources=llm_sources, is_fallback=False)