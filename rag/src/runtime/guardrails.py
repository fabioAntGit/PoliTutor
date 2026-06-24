"""
Guardrails Module.

Protects the Socratic tutor pipeline with input and output guardrails.

Public entry points (used by the RAG engine):
    apply_input_guardrails   sanitizes + validates the query before retrieval,
                             returning the clean query and an optional block response.
    apply_output_guardrail   replaces non-Socratic answers with a Socratic redirect.

Internal checks: _sanitize_input, _validate_input, _detect_prompt_injection,
_detect_code_request, _detect_direct_answer.
"""

import re
import logging

from ..shared.config import (
    CODE_REQUEST_PATTERNS,
    DIRECT_ANSWER_MIN_LENGTH,
    DIRECT_ANSWER_SIGNALS,
    INJECTION_PATTERNS,
    QUERY_MAX_LENGTH,
    QUERY_MIN_LENGTH,
    SOCRATIC_REDIRECT,
)
from contracts.rag.models import TutorResponse

logger = logging.getLogger(__name__)


def _sanitize_input(query: str) -> str:
    """
    Removes characters / sequences that could interfere with the prompt
    template delimiters (``<user_question>``, ``<rag_context>``).

    Returns:
        The cleaned query string.
    """
    sanitized = re.sub(r"</?[a-zA-Z_]+>", "", query)
    return sanitized.strip()


def _validate_input(query: str) -> tuple[bool, str]:
    """
    Validates the student's query before it enters the retrieval pipeline.

    Checks applied (in order):
        1. Empty / whitespace-only query.
        2. Too short (< QUERY_MIN_LENGTH meaningful characters).
        3. Too long (> QUERY_MAX_LENGTH characters).

    Returns:
        A tuple (is_valid, reason).
        - is_valid=True  → query is safe; ``reason`` is empty.
        - is_valid=False → query is blocked; ``reason`` explains why.
    """
    stripped = query.strip()

    if not stripped:
        return False, "A pergunta está vazia. Por favor, escreva a sua dúvida."

    if len(stripped) < QUERY_MIN_LENGTH:
        return False, (
            f"A pergunta é demasiado curta (mínimo {QUERY_MIN_LENGTH} caracteres). "
            "Tente formular uma dúvida mais completa."
        )

    if len(stripped) > QUERY_MAX_LENGTH:
        return False, (
            f"A pergunta excede o limite de {QUERY_MAX_LENGTH} caracteres. "
            "Por favor, reduza o texto e foque-se na dúvida principal."
        )

    return True, ""


def _detect_prompt_injection(query: str) -> tuple[bool, str]:
    """
    Detects attempts to override the Socratic system prompt.

    Scans the query against a curated list of injection patterns
    (Portuguese & English).

    Returns:
        (is_injection, message).
        - is_injection=True  → query is blocked.
        - is_injection=False → query is safe.
    """
    query_lower = query.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query_lower):
            logger.warning("[GUARDRAIL] Prompt injection detected: %s", query[:120])
            return True, (
                "A tua pergunta parece tentar alterar o meu comportamento. "
                "Sou um tutor Socrático - reformula a tua dúvida sobre a matéria."
            )
    return False, ""


def _detect_code_request(query: str) -> tuple[bool, str]:
    """
    Detects explicit requests for complete code, solutions, or implementations.

    Returns:
        (is_code_request, message).
        - is_code_request=True  → query is blocked.
        - is_code_request=False → query is safe.
    """
    query_lower = query.lower()
    for pattern in CODE_REQUEST_PATTERNS:
        if re.search(pattern, query_lower):
            logger.warning("[GUARDRAIL] Code request detected: %s", query[:120])
            return True, (
                "Não forneço código completo - sou um tutor Socrático!\n"
                "Reformula a tua pergunta em termos do conceito que queres perceber. "
                "Por exemplo: 'Como funciona o algoritmo X?' ou "
                "'Qual é a lógica por trás de Y?'"
            )
    return False, ""


def apply_input_guardrails(query: str) -> tuple[str, TutorResponse | None]:
    """
    INPUT guardrails applied before retrieval: sanitizes the query and runs the
    block checks (length, prompt injection, code request).
    """
    query = _sanitize_input(query)

    is_valid, reason = _validate_input(query)
    if not is_valid:
        return query, TutorResponse(answer=reason, sources=[], is_fallback=True, is_guardrail=True)

    is_injection, reason = _detect_prompt_injection(query)
    if is_injection:
        return query, TutorResponse(answer=reason, sources=[], is_fallback=True, is_guardrail=True)

    is_code_req, reason = _detect_code_request(query)
    if is_code_req:
        return query, TutorResponse(answer=reason, sources=[], is_fallback=True, is_guardrail=True)

    return query, None


def _detect_direct_answer(answer: str) -> bool:
    """
    Checks whether the LLM response contains signs of a non-Socratic,
    direct answer.

    Heuristics:
        1. Matches against known "direct answer" linguistic patterns.
        2. Flags responses longer than 100 chars that contain no '?'
           (Socratic responses should include guiding questions).

    Returns:
        True if the answer appears to be a direct/non-Socratic response.
    """
    answer_lower = answer.lower()

    for pattern in DIRECT_ANSWER_SIGNALS:
        if re.search(pattern, answer_lower):
            logger.warning("[GUARDRAIL] Direct answer signal detected in output.")
            return True

    if len(answer.strip()) > DIRECT_ANSWER_MIN_LENGTH and "?" not in answer:
        logger.warning("[GUARDRAIL] Non-Socratic output: long response without a guiding question.")
        return True

    return False


def apply_output_guardrail(response: TutorResponse) -> TutorResponse:
    """
    OUTPUT guardrail applied after generation. If a genuine answer looks
    non-Socratic, replaces it with the Socratic redirect while preserving the
    sources. Fallback / error responses are passed through untouched.
    """
    if not response.is_fallback and _detect_direct_answer(response.answer):
        logger.warning("[GUARDRAIL] Output guardrail triggered — replacing with Socratic redirect.")
        return TutorResponse(
            answer=SOCRATIC_REDIRECT,
            sources=response.sources,
            is_fallback=False,
            is_output_guardrail=True,
            is_retrieval_fallback=response.is_retrieval_fallback,
        )

    return response
