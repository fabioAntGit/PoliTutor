"""Integration tests for user memory persistence and service logic."""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from app.backend.core.config import (
    MAX_MEMORIES_PER_COURSE,
    MEMORY_DELETE_IMPORTANCE_THRESHOLD,
    MEMORY_MIN_IMPORTANCE_FOR_INJECTION,
    MEMORY_TTL_BY_TYPE,
)
from app.backend.repositories.user_memory import UserMemoryRepository
from app.backend.gateways.interfaces.model_client import IModelClient
from app.backend.schemas.memory.models import UserMemory
from app.backend.services.user_memory import UserMemoryService

from .factories import insert_memory


@pytest.fixture
def repo(db) -> UserMemoryRepository:
    return UserMemoryRepository(db)


@pytest.fixture
def model_client() -> MagicMock:
    return MagicMock(spec=IModelClient)


@pytest.fixture
def service(repo, model_client) -> UserMemoryService:
    return UserMemoryService(repo=repo, model_client=model_client)


def _llm_returning(memories: list[dict], *, fenced: bool = False):
    """Build a fake model_client.call that returns the given memories as JSON."""
    payload = json.dumps({"memories": memories})
    if fenced:
        payload = f"```json\n{payload}\n```"

    def _fake(prompt, *args, **kwargs) -> str:
        return payload

    return _fake


class TestRepository:
    async def test_create_and_get_by_id_roundtrip(self, repo, db):
        now = datetime.now(timezone.utc)
        mem = UserMemory(
            id="m1", user_id="u1", course="ed", type="goal",
            topic="recursion", content="struggles with recursion",
            importance=7.5, last_seen_at=now, created_at=now,
        )
        await repo.create(mem)

        got = await repo.get_by_id("m1")
        assert got is not None
        assert got.id == "m1"
        assert got.topic == "recursion"
        assert got.importance == 7.5

    async def test_get_by_key_matches_exact_tuple(self, repo, db):
        await insert_memory(db, mem_id="m1", user_id="u1", course="ed", mem_type="goal", topic="loops")
        await insert_memory(db, mem_id="m2", user_id="u1", course="ed", mem_type="preference", topic="loops")

        hit = await repo.get_by_key("u1", "ed", "goal", "loops")
        miss = await repo.get_by_key("u1", "ed", "difficulty", "loops")

        assert hit is not None and hit.id == "m1"
        assert miss is None

    async def test_get_by_user_and_course_is_scoped(self, repo, db):
        await insert_memory(db, mem_id="m1", user_id="u1", course="ed")
        await insert_memory(db, mem_id="m2", user_id="u1", course="poo")  # other course
        await insert_memory(db, mem_id="m3", user_id="u2", course="ed")  # other user

        found = await repo.get_by_user_and_course("u1", "ed")

        assert {m.id for m in found} == {"m1"}

    async def test_update_modifies_fields(self, repo, db):
        await insert_memory(db, mem_id="m1", user_id="u1", course="ed", importance=5.0)

        await repo.update("m1", {"importance": 9.0})

        assert (await repo.get_by_id("m1")).importance == 9.0

    async def test_delete_removes_document(self, repo, db):
        await insert_memory(db, mem_id="m1", user_id="u1", course="ed")

        await repo.delete("m1")

        assert await repo.get_by_id("m1") is None


class TestListAndDelete:
    async def test_list_returns_user_course_memories(self, service, db):
        await insert_memory(db, mem_id="m1", user_id="u1", course="ed")
        await insert_memory(db, mem_id="m2", user_id="u1", course="ed")
        await insert_memory(db, mem_id="m3", user_id="u2", course="ed")

        memories = await service.list_memories("u1", "ed")

        assert {m.id for m in memories} == {"m1", "m2"}

    async def test_delete_own_memory_returns_true(self, service, repo, db):
        await insert_memory(db, mem_id="m1", user_id="u1", course="ed")

        assert await service.delete_memory("u1", "m1") is True
        assert await repo.get_by_id("m1") is None

    async def test_delete_other_users_memory_returns_false(self, service, repo, db):
        await insert_memory(db, mem_id="m1", user_id="u2", course="ed")

        assert await service.delete_memory("u1", "m1") is False
        assert await repo.get_by_id("m1") is not None  # untouched

    async def test_delete_missing_memory_returns_false(self, service):
        assert await service.delete_memory("u1", "nope") is False


class TestContextForPrompt:
    async def test_returns_none_when_nothing_relevant(self, service, db):
        below = MEMORY_MIN_IMPORTANCE_FOR_INJECTION - 1.0
        await insert_memory(db, mem_id="m1", user_id="u1", course="ed", importance=below)

        assert await service.get_context_for_prompt("u1", "ed") is None

    async def test_includes_only_relevant_memories(self, service, db):
        await insert_memory(
            db, mem_id="hi", user_id="u1", course="ed",
            importance=MEMORY_MIN_IMPORTANCE_FOR_INJECTION + 1.0,
            topic="recursion", content="keep me",
        )
        await insert_memory(
            db, mem_id="lo", user_id="u1", course="ed",
            importance=MEMORY_MIN_IMPORTANCE_FOR_INJECTION - 1.0,
            topic="loops", content="drop me",
        )

        context = await service.get_context_for_prompt("u1", "ed")

        assert context is not None
        assert "[Student Memory]" in context
        assert "keep me" in context
        assert "drop me" not in context


class TestDecay:
    async def test_recent_memory_keeps_importance(self, service, repo, db):
        ttl_days = MEMORY_TTL_BY_TYPE["preference"] / 86400
        await insert_memory(
            db, mem_id="m1", user_id="u1", course="ed", mem_type="preference",
            importance=5.0, last_seen_days_ago=ttl_days / 2,  # still within TTL
        )

        await service._apply_decay("u1", "ed")

        assert (await repo.get_by_id("m1")).importance == 5.0

    async def test_expired_memory_loses_importance(self, service, repo, db):
        ttl_days = MEMORY_TTL_BY_TYPE["goal"] / 86400  # 7 days
        await insert_memory(
            db, mem_id="m1", user_id="u1", course="ed", mem_type="goal",
            importance=5.0, last_seen_days_ago=ttl_days + 7,  # one week past expiry
        )

        await service._apply_decay("u1", "ed")

        decayed = await repo.get_by_id("m1")
        assert decayed is not None  # not evicted yet
        assert decayed.importance < 5.0
        assert decayed.importance >= MEMORY_DELETE_IMPORTANCE_THRESHOLD

    async def test_heavily_decayed_memory_is_evicted(self, service, repo, db):
        ttl_days = MEMORY_TTL_BY_TYPE["goal"] / 86400
        await insert_memory(
            db, mem_id="m1", user_id="u1", course="ed", mem_type="goal",
            importance=0.6, last_seen_days_ago=ttl_days + 28,  # long past expiry
        )

        await service._apply_decay("u1", "ed")

        assert await repo.get_by_id("m1") is None


class TestExtractAndUpsert:
    async def test_creates_new_memories(self, service, repo, db, model_client):
        model_client.call.side_effect = _llm_returning([
            {"type": "difficulty", "topic": "Recursion", "content": "struggles", "importance": 7.0},
            {"type": "goal", "topic": "Pointers", "content": "wants to master", "importance": 6.0},
        ])

        await service.extract_and_upsert("u1", "ed", summary="...")

        stored = await repo.get_by_user_and_course("u1", "ed")
        by_topic = {m.topic: m for m in stored}
        assert set(by_topic) == {"recursion", "pointers"}  # topics normalized to lowercase
        assert by_topic["recursion"].importance == 7.0

    async def test_filters_out_invalid_entries(self, service, repo, db, model_client):
        model_client.call.side_effect = _llm_returning([
            {"type": "difficulty", "topic": "ok", "content": "valid", "importance": 5.0},
            {"type": "bogus", "topic": "x", "content": "bad type", "importance": 5.0},
            {"type": "goal", "topic": "", "content": "no topic", "importance": 5.0},
            {"type": "goal", "topic": "y", "content": "out of range", "importance": 99.0},
        ])

        await service.extract_and_upsert("u1", "ed", summary="...")

        stored = await repo.get_by_user_and_course("u1", "ed")
        assert {m.topic for m in stored} == {"ok"}

    async def test_blends_existing_memory(self, service, repo, db, model_client):
        await insert_memory(
            db, mem_id="m1", user_id="u1", course="ed",
            mem_type="goal", topic="recursion", content="old", importance=4.0,
        )
        model_client.call.side_effect = _llm_returning([
            {"type": "goal", "topic": "recursion", "content": "new", "importance": 8.0},
        ])

        await service.extract_and_upsert("u1", "ed", summary="...")

        merged = await repo.get_by_key("u1", "ed", "goal", "recursion")
        assert merged.importance == 6.0  # (4 + 8) / 2
        assert merged.content == "new"  # updated because new importance was higher

    async def test_evicts_lowest_when_cap_reached(self, service, repo, db, model_client):
        for i in range(MAX_MEMORIES_PER_COURSE):
            await insert_memory(
                db, mem_id=f"m{i:02d}", user_id="u1", course="ed",
                mem_type="preference", topic=f"t{i:02d}", importance=(i + 1) * 0.5,
            )
        model_client.call.side_effect = _llm_returning([
            {"type": "preference", "topic": "fresh", "content": "new", "importance": 9.0},
        ])

        await service.extract_and_upsert("u1", "ed", summary="...")

        stored = await repo.get_by_user_and_course("u1", "ed")
        topics = {m.topic for m in stored}
        assert len(stored) == MAX_MEMORIES_PER_COURSE  # capped
        assert "fresh" in topics
        assert "t00" not in topics  # lowest-importance evicted

    async def test_parses_fenced_json(self, service, repo, db, model_client):
        model_client.call.side_effect = _llm_returning(
            [{"type": "goal", "topic": "loops", "content": "c", "importance": 5.0}],
            fenced=True,
        )

        await service.extract_and_upsert("u1", "ed", summary="...")

        assert await repo.get_by_key("u1", "ed", "goal", "loops") is not None

    async def test_llm_failure_is_swallowed(self, service, repo, db, model_client):
        def _boom(prompt, *args, **kwargs):
            raise RuntimeError("LLM down")

        model_client.call.side_effect = _boom

        await service.extract_and_upsert("u1", "ed", summary="...")  # must not raise

        assert await repo.get_by_user_and_course("u1", "ed") == []

    async def test_empty_response_is_noop(self, service, repo, db, model_client):
        model_client.call.side_effect = lambda *a, **k: ""

        await service.extract_and_upsert("u1", "ed", summary="...")

        assert await repo.get_by_user_and_course("u1", "ed") == []

    async def test_unparseable_json_is_ignored(self, service, repo, db, model_client):
        model_client.call.side_effect = lambda *a, **k: "this is not valid json {"

        await service.extract_and_upsert("u1", "ed", summary="...")

        assert await repo.get_by_user_and_course("u1", "ed") == []

    async def test_upsert_error_is_swallowed(self, service, repo, db, monkeypatch, model_client):
        async def _boom_create(*args, **kwargs):
            raise RuntimeError("db write failed")

        monkeypatch.setattr(service.repo, "create", _boom_create)
        model_client.call.side_effect = _llm_returning([
            {"type": "goal", "topic": "loops", "content": "c", "importance": 5.0},
        ])

        await service.extract_and_upsert("u1", "ed", summary="...")  # must not raise

        assert await repo.get_by_user_and_course("u1", "ed") == []
