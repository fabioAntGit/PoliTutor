import logging

from fastapi import APIRouter

from app.backend.schemas.ask import AskRequest, AskResponseOut, SourceOut
from app.backend.services.messages import ask_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/ask", response_model=AskResponseOut)
def ask_endpoint(body: AskRequest):

    response = ask_message(body)

    return AskResponseOut(
        answer=response.answer,
        sources=[SourceOut(filename=s.filename, pages=s.pages) for s in response.sources],
        is_fallback=response.is_fallback,
        guardrail_triggered=response.guardrail_triggered,
    )
