"""
Poli Tutor — FastAPI Backend.

Exposes the RAG pipeline over HTTP so the frontend can query it.

Inside rag/src run with:
    python -m uvicorn api:app --reload --port 8000
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import AnyHttpUrl, BaseModel, Field, field_validator

from config import QUERY_MAX_LENGTH, SOCRATIC_REDIRECT
from retrieval import ask
from projects import PROJECT_REGISTRY

logger = logging.getLogger(__name__)

app = FastAPI(title="Poli Tutor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler: logs the real error but never leaks internals to the client."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})

class AskRequest(BaseModel):
    project_id: str = Field(pattern=r"^[a-z0-9\-]+$", max_length=64)
    question: str = Field(min_length=1, max_length=QUERY_MAX_LENGTH)
    iaedu_endpoint: AnyHttpUrl
    iaedu_api_key: str = Field(pattern=r"^sk-usr-[a-z0-9]+$", max_length=128)
    iaedu_channel_id: str = Field(pattern=r"^[a-z0-9]+$", max_length=64)

    @field_validator("iaedu_api_key", "iaedu_channel_id", mode="before")
    @classmethod
    def strip_credentials(cls, v: str) -> str:
        return v.strip()

class SourceOut(BaseModel):
    filename: str
    pages: list[int]

class AskResponseOut(BaseModel):
    answer: str
    sources: list[SourceOut]
    is_fallback: bool
    guardrail_triggered: bool

@app.post("/ask", response_model=AskResponseOut)
def ask_endpoint(body: AskRequest):
    project = PROJECT_REGISTRY.get(body.project_id)

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{body.project_id}' not found.")

    response = ask(
        project.course_code,
        body.question,
        collection_name=project.collection_name,
        iaedu_url=str(body.iaedu_endpoint),
        iaedu_channel_id=body.iaedu_channel_id,
        iaedu_api_key=body.iaedu_api_key,
    )

    return AskResponseOut(
        answer=response.answer,
        sources=[SourceOut(filename=s.filename, pages=s.pages) for s in response.sources],
        is_fallback=response.is_fallback,
        guardrail_triggered=(response.answer == SOCRATIC_REDIRECT),
    )
#falta fazer o endpoint de get messages de uma conversa