from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
import redis.asyncio as redis

from app.backend.core.config import MONGO_DB, MONGO_URI, REDIS_HOST, REDIS_PORT

_client: AsyncMongoClient | None = None
_db: AsyncDatabase | None = None
_db_deprecated: AsyncDatabase | None = None
_redis: redis.Redis | None = None

DEPRECATED_RETENTION_SECONDS = 30 * 24 * 60 * 60  # 30 dias
DEPRECATED_COLLECTIONS = ("users", "chats", "messages", "user_memory", "reports")


async def connect_to_mongo() -> None:
    global _client, _db, _db_deprecated
    _client = AsyncMongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
    await _client.admin.command("ping")
    _db = _client[MONGO_DB]
    _db_deprecated = _client[f"{MONGO_DB}_deprecated"]
    await _ensure_indexes(_db)
    await _ensure_deprecated_indexes(_db_deprecated)


async def _ensure_indexes(db: AsyncDatabase) -> None:
    await db["chats"].create_index("user_id")
    await db["chats"].create_index("course_id")
    await db["chats"].create_index([("course_id", 1), ("created_at", -1)])
    await db["messages"].create_index([("role", 1), ("conversation_id", 1)])
    await db["messages"].create_index([("role", 1), ("created_at", 1)])
    await db["users"].create_index("email", unique=True)
    await db["users"].create_index("username", unique=True)
    await db["user_memory"].create_index([("user_id", 1), ("course_id", 1)])
    await db["user_memory"].create_index([("user_id", 1), ("course_id", 1), ("type", 1), ("topic", 1)], unique=True)

async def _ensure_deprecated_indexes(db: AsyncDatabase) -> None:
    for name in DEPRECATED_COLLECTIONS:
        await db[name].create_index(
            "deleted_at",
            expireAfterSeconds=DEPRECATED_RETENTION_SECONDS,
        )

async def connect_to_redis() -> None:
    global _redis
    _redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    await _redis.ping()


def get_db() -> AsyncDatabase:
    if _db is None:
        raise RuntimeError("MongoDB not initialized")
    return _db


def get_deprecated_db() -> AsyncDatabase:
    if _db_deprecated is None:
        raise RuntimeError("MongoDB deprecated database not initialized")
    return _db_deprecated


def get_redis() -> redis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized")
    return _redis


async def close_mongo() -> None:
    if _client is not None:
        await _client.close()


async def close_redis() -> None:
    if _redis is not None:
        await _redis.aclose()
