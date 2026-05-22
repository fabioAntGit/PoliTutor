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

from app.backend.api.v1.endpoints.analytics import router as analytics_router
from app.backend.api.v1.endpoints.authentication import router as authentication_router
from app.backend.api.v1.endpoints.chats import router as chats_router
from app.backend.api.v1.endpoints.courses import router as courses_router
from app.backend.api.v1.endpoints.memory import router as memory_router
from app.backend.api.v1.endpoints.messages import router as messages_router
from app.backend.api.v1.endpoints.reports import router as reports_router
from app.backend.api.v1.endpoints.users import router as users_router
from app.backend.core.database import close_mongo, connect_to_mongo, connect_to_redis, close_redis
from app.backend.core.exceptions import AppError
from app.backend.schemas.shared.api_error import ApiError
from rag.src.ingestion.embedding import get_embedder
from rag.src.runtime.reranker import get_reranker

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
    logger.info("Connecting to MongoDB...")
    await connect_to_mongo()
    logger.info("Connecting to Redis...")
    await connect_to_redis()
    logger.info("Pre-loading embedding and reranker models...")
    get_embedder()
    get_reranker()
    logger.info("Models loaded and ready.")


app.include_router(authentication_router, prefix="/api/v1", tags=["auth"])
app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(courses_router, prefix="/api/v1", tags=["courses"])
app.include_router(chats_router, prefix="/api/v1", tags=["chats"])
app.include_router(messages_router, prefix="/api/v1", tags=["messages"])
app.include_router(reports_router, prefix="/api/v1", tags=["reports"])
app.include_router(analytics_router, prefix="/api/v1", tags=["dashboard"])
app.include_router(memory_router, prefix="/api/v1", tags=["memory"])

@app.on_event("shutdown")
async def shutdown_event():
    await close_mongo()
    await close_redis()
