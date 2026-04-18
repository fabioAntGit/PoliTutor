from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.backend.core.config import MONGO_DB, MONGO_URI

_client: AsyncMongoClient | None = None
_db: AsyncDatabase | None = None


async def connect_to_mongo() -> None:
    global _client, _db
    _client = AsyncMongoClient(MONGO_URI)
    await _client.admin.command("ping")
    _db = _client[MONGO_DB]


def get_db() -> AsyncDatabase:
    if _db is None:
        raise RuntimeError("MongoDB not initialized")
    return _db


async def close_mongo() -> None:
    if _client is not None:
        await _client.close()
