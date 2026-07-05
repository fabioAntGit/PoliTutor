"""
Poli Tutor - FastAPI Backend.

Exposes the RAG pipeline over HTTP so the frontend can query it.

Run from the repository root with:
    python -m uvicorn app.backend.main:app --reload --port 8000
"""

import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.backend.core.rate_limit import limiter, rate_limit_exceeded_handler
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
from app.backend.core.logging_config import setup_logging
from app.backend.api.deps import get_rag_engine

logger = logging.getLogger(__name__)

setup_logging()

RAG_PRELOAD = os.getenv("RAG_PRELOAD", "1") != "0"

OPENAPI_TAGS = [
    {
        "name": "auth",
        "description": (
            "Authentication and session management. Log in to obtain a JWT access "
            "token, log out to revoke it, and change the current user's password. "
        ),
    },
    {
        "name": "users",
        "description": (
            "Create, list, fetch, update and delete user "
            "accounts. All routes are admin-only, except self-service account "
            "deletion (DELETE /users/me)."
        ),
    },
    {
        "name": "courses",
        "description": (
            "Course catalog. List the courses available to the caller, and create, "
            "update or delete courses."
        ),
    },
    {
        "name": "chats",
        "description": (
            "Conversations between a student and the tutor. Create a conversation "
            "for a course, list the caller's conversations, and fetch or delete a "
            "single one."
        ),
    },
    {
        "name": "messages",
        "description": (
            "Tutoring messages. Send a question to a conversation and receive the "
            "RAG-powered tutor answer with its cited sources."
        ),
    },
    {
        "name": "reports",
        "description": (
            "Message reports. Flag or unflag an assistant answer as problematic. "
        ),
    },
    {
        "name": "dashboard",
        "description": (
            "Teacher dashboard analytics. Read-only aggregated usage metrics "
            "(conversations, active students, message volume, activity over time, "
            "top topics and most-referenced sources). Restricted to teacher and "
            "admin roles, results are scoped to the courses the caller can access."
        ),
    },
    {
        "name": "memory",
        "description": (
            "Long-term student memory. List and delete the per-course memories the "
            "tutor keeps about the caller to personalise future answers."
        ),
    },
]

app = FastAPI(title="PoliTutor API", version="1.0.0", openapi_tags=OPENAPI_TAGS)

# Fallback for routes without a tighter @limiter.limit.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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
    if RAG_PRELOAD:
        logger.info("Pre-loading embedding and reranker models...")
        rag_engine = get_rag_engine()
        rag_engine.preload_models()
        logger.info("Models loaded and ready.")
    else:
        logger.info("RAG_PRELOAD=0 — skipping model pre-load (lean backend).")


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
