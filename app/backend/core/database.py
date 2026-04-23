from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
import redis.asyncio as redis

from app.backend.core.config import MONGO_DB, MONGO_URI, REDIS_HOST, REDIS_PORT

_client: AsyncMongoClient | None = None
_db: AsyncDatabase | None = None
_redis: redis.Redis | None = None


async def connect_to_mongo() -> None:
    global _client, _db
    _client = AsyncMongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
    await _client.admin.command("ping")
    _db = _client[MONGO_DB]


async def connect_to_redis() -> None:
    global _redis
    _redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    await _redis.ping()


def get_db() -> AsyncDatabase:
    if _db is None:
        raise RuntimeError("MongoDB not initialized")
    return _db


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
