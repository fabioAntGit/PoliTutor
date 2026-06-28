"""Input and output guardrails for the Socratic tutor."""

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
    """Remove fake XML tags before prompt construction."""
    sanitized = re.sub(r"</?[a-zA-Z_]+>", "", query)
    return sanitized.strip()


def _validate_input(query: str) -> tuple[bool, str]:
    """Check basic query length limits."""
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
    """Detect prompt-injection attempts."""
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
    """Detect requests for complete code or ready-made solutions."""
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
    """Apply all input guardrails before retrieval."""
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
    """Detect non-Socratic direct answers using simple heuristics."""
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
    """Replace non-Socratic answers while preserving sources."""
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
