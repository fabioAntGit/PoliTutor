"""
Poli Tutor - FastAPI Backend.

Exposes the RAG pipeline over HTTP so the frontend can query it.

Run from the repository root with:
    python -m uvicorn app.backend.main:app --reload --port 8000
"""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.backend.api.v1.endpoints.chats import router as chats_router
from app.backend.api.v1.endpoints.messages import router as messages_router
from app.backend.api.v1.endpoints.projects import router as projects_router
from app.backend.core.database import close_mongo, connect_to_mongo, connect_to_redis, close_redis
from app.backend.core.exceptions import AppError
from app.backend.schemas.shared.api_error import ApiError

logger = logging.getLogger(__name__)

app = FastAPI(title="Poli Tutor API", version="1.0.0")

DEV_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=DEV_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    error = ApiError(code="internal_error", message="Internal server error.")
    return JSONResponse(status_code=500, content=error.model_dump())


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    error = ApiError(code=exc.code, message=exc.message, details=exc.details)
    return JSONResponse(status_code=exc.status_code, content=error.model_dump())


@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    await connect_to_redis()


app.include_router(chats_router, prefix="/api/v1")
app.include_router(messages_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")


@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo()
    await close_redis()
