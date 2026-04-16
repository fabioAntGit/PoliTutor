"""
Guardrails Module.

Provides input validation, prompt-injection detection, output verification,
and sanitization functions that protect the Socratic tutor pipeline.

INPUT guardrails (applied before retrieval):
    sanitize_input          strips XML-like tags that could hijack prompt delimiters.
    validate_input          checks empty / too-short / too-long queries.
    detect_prompt_injection blocks attempts to override Socratic rules.
    detect_code_request     blocks explicit requests for complete code/solutions.

OUTPUT guardrails (applied after generation):
    detect_direct_answer    flags responses that appear non-Socratic.
"""

import re
import logging

from .config import (
    CODE_REQUEST_PATTERNS,
    DIRECT_ANSWER_SIGNALS,
    INJECTION_PATTERNS,
    QUERY_MAX_LENGTH,
    QUERY_MIN_LENGTH,
)

logger = logging.getLogger(__name__)

def sanitize_input(query: str) -> str:
    """
    Removes characters / sequences that could interfere with the prompt
    template delimiters (``<user_question>``, ``<rag_context>``).

    Returns:
        The cleaned query string.
    """
    sanitized = re.sub(r"</?[a-zA-Z_]+>", "", query)
    return sanitized.strip()


def validate_input(query: str) -> tuple[bool, str]:
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


def detect_prompt_injection(query: str) -> tuple[bool, str]:
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


def detect_code_request(query: str) -> tuple[bool, str]:
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


def detect_direct_answer(answer: str) -> bool:
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

    if "?" not in answer and len(answer) > 100:
        logger.warning("[GUARDRAIL] Output has no guiding questions (len=%d).", len(answer))
        return True

    return False

def where_filter(course: str) -> dict:
    return {"course": course.strip().lower()}
