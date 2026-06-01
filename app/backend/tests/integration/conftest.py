"""
Shared fixtures for the backend integration tests.

Strategy: a **real**, ephemeral MongoDB (Testcontainers) starts once per test
session and is torn down at the end. Each test gets a clean database, so test
ordering never influences the result.

Two layers build on this:
- Repository/service tests only need `pymongo` + `testcontainers`.
- Route tests additionally import the FastAPI app and drive it in-process with
  an httpx client, overriding the DB/Redis dependencies to point at the test
  database (never production).
"""

import os

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("JWT_SECRET_KEY", "integration-test-secret-key-0123456789")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pymongo import AsyncMongoClient

from testcontainers.mongodb import MongoDbContainer

_TEST_DB_NAME = "poli_tutor_test"


@pytest.fixture(scope="session")
def mongo_url() -> str:
    with MongoDbContainer("mongo:7.0") as mongo:
        yield mongo.get_connection_url()


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

class _FakeRedisRepo:
    """Stand-in for the Redis repository: no token is ever blacklisted."""

    async def is_token_blacklisted(self, token: str) -> bool:
        return False


@pytest_asyncio.fixture
async def api_client(db):
    """In-process httpx client against the app, with DB/Redis pointed at the test DB."""
    from app.backend.main import app
    from app.backend.api.deps import get_db, get_redis_repository

    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_redis_repository] = lambda: _FakeRedisRepo()
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def make_token():
    """Factory for real JWTs, so the auth guards run for real in route tests."""
    import jwt

    from app.backend.core.config import JWT_ALGORITHM, JWT_SECRET_KEY

    def _make(role: str = "teacher", courses: list[str] | None = None, **extra) -> str:
        payload = {
            "id": "user-1",
            "username": "prof",
            "full_name": "Prof Example",
            "role": role,
            "courses": courses or [],
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
