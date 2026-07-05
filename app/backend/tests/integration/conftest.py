"""Ephemeral MongoDB and Redis via Testcontainers; one clean DB per test."""
import os

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("JWT_SECRET_KEY", "integration-test-secret-key-0123456789")

from datetime import datetime, timedelta, timezone

import jwt
import pytest
import pytest_asyncio
import redis.asyncio as redis_async
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

from app.backend.api.deps import get_db, get_deprecated_db, get_cache_repository
from app.backend.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.backend.main import app
from app.backend.repositories.redis import RedisRepository

_TEST_DB_NAME = "poli_tutor_test"


@pytest.fixture(scope="session")
def mongo_url() -> str:
    with MongoDbContainer("mongo:7.0") as mongo:
        yield mongo.get_connection_url()


@pytest.fixture(scope="session")
def redis_url() -> tuple[str, int]:
    with RedisContainer("redis:7-alpine") as redis:
        yield redis.get_container_host_ip(), int(redis.get_exposed_port(6379))


@pytest_asyncio.fixture
async def db(mongo_url):
    """Clean test database bound to the test's own event loop."""
    client = AsyncMongoClient(mongo_url)
    database = client[_TEST_DB_NAME]

    for name in await database.list_collection_names():
        await database[name].delete_many({})
    try:
        yield database
    finally:
        await client.close()


@pytest_asyncio.fixture
async def redis_repo(redis_url):
    """Real Redis repository backed by an ephemeral Testcontainers Redis."""
    host, port = redis_url
    client = redis_async.Redis(host=host, port=port, decode_responses=True)
    await client.flushdb()
    try:
        yield RedisRepository(client)
    finally:
        await client.flushdb()
        await client.aclose()


@pytest_asyncio.fixture
async def api_client(db, redis_repo):
    """In-process httpx client against the app, with DB/Redis pointed at the test DB.

    Rate limiting is turned off so tests can hammer endpoints freely without
    tripping the per-minute limits.
    """
    app.state.limiter.enabled = False
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_deprecated_db] = lambda: db.client[f"{_TEST_DB_NAME}_deprecated"]
    app.dependency_overrides[get_cache_repository] = lambda: redis_repo
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_token():
    """Factory for real JWTs, so the auth guards run for real in route tests."""

    def _make(role: str = "teacher", courses: list[str] | None = None, **extra) -> str:
        payload = {
            "id": "user-1",
            "username": "prof",
            "full_name": "Prof Example",
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            **extra,
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return _make


@pytest.fixture
def auth_header(make_token):
    """Convenience: Authorization header for a given role/courses."""

    def _header(role: str = "teacher", courses: list[str] | None = None, **extra) -> dict:
        return {"Authorization": f"Bearer {make_token(role=role, courses=courses, **extra)}"}

    return _header
