"""
Poli Tutor — FastAPI Backend.

Exposes the RAG pipeline over HTTP so the frontend can query it.

Run from the repository root with:
    python -m uvicorn app.backend.main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.backend.api.v1.endpoints.projects import router as projects_router
from app.backend.api.v1.endpoints.messages import router as messages_router

logger = logging.getLogger(__name__)

app = FastAPI(title="Poli Tutor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


app.include_router(messages_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
