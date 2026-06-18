from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from app.backend.repositories.interfaces.user_memory_repository import IUserMemoryRepository
from app.backend.schemas.memory.models import UserMemory
from app.backend.services.user_memory import UserMemoryService


def _memory(**kwargs) -> UserMemory:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id="mem_1",
        user_id="u1",
        course="Math",
        type="goal",
        topic="exam",
        content="wants to pass",
        importance=5.0,
        last_seen_at=now,
        created_at=now,
    )
    defaults.update(kwargs)
    return UserMemory(**defaults)


@pytest.fixture
def repo():
    return AsyncMock(spec=IUserMemoryRepository)


@pytest.fixture
def service(repo):
    return UserMemoryService(repo)


async def test_context_includes_only_important_memories(service, repo):
    repo.get_by_user_and_course.return_value = [
        _memory(id="m1", importance=5.0, topic="relevant"),
        _memory(id="m2", importance=1.0, topic="trivial"),
    ]
    context = await service.get_context_for_prompt("u1", "Math")
    assert "relevant" in context
    assert "trivial" not in context


async def test_context_none_when_nothing_relevant(service, repo):
    repo.get_by_user_and_course.return_value = [_memory(importance=1.0)]
    assert await service.get_context_for_prompt("u1", "Math") is None


async def test_list_memories_delegates_to_repo(service, repo):
    memories = [_memory(id="m1"), _memory(id="m2")]
    repo.get_by_user_and_course.return_value = memories
    result = await service.list_memories("u1", "Math")
    assert result == memories
    repo.get_by_user_and_course.assert_awaited_once_with("u1", "Math")


async def test_delete_returns_false_for_wrong_owner(service, repo):
    repo.get_by_id.return_value = _memory(user_id="another_user")
    assert await service.delete_memory("u1", "mem_1") is False
    repo.delete.assert_not_awaited()


async def test_delete_returns_false_when_not_found(service, repo):
    repo.get_by_id.return_value = None
    assert await service.delete_memory("u1", "mem_1") is False
    repo.delete.assert_not_awaited()


async def test_delete_succeeds_for_owner(service, repo):
    repo.get_by_id.return_value = _memory(id="mem_1", user_id="u1")
    assert await service.delete_memory("u1", "mem_1") is True
    repo.delete.assert_awaited_once_with("mem_1")


async def test_upsert_blends_importance_and_updates_content(service, repo):
    repo.get_by_key.return_value = _memory(id="m1", importance=4.0, content="old")
    mem = {"type": "goal", "topic": "exam", "content": "new", "importance": 8.0}
    await service._upsert_one("u1", "Math", mem)

    mem_id, updates = repo.update.call_args[0]
    assert mem_id == "m1"
    assert updates["importance"] == 6.0  # (4 + 8) / 2
    assert updates["content"] == "new" 


async def test_upsert_keeps_content_when_new_less_important(service, repo):
    repo.get_by_key.return_value = _memory(id="m1", importance=8.0, content="old")
    mem = {"type": "goal", "topic": "exam", "content": "new", "importance": 4.0}
    await service._upsert_one("u1", "Math", mem)

    _, updates = repo.update.call_args[0]
    assert "content" not in updates


async def test_upsert_creates_new_with_normalized_topic(service, repo):
    repo.get_by_key.return_value = None
    repo.get_by_user_and_course.return_value = []
    mem = {"type": "goal", "topic": "  Final Exam ", "content": "pass", "importance": 7.0}
    await service._upsert_one("u1", "Math", mem)

    created = repo.create.call_args[0][0]
    assert created.topic == "final exam"
    assert created.importance == 7.0
    assert created.user_id == "u1"


async def test_upsert_evicts_lowest_when_cap_reached(service, repo):
    repo.get_by_key.return_value = None
    full = [_memory(id=f"m{i}", importance=0.5 + i * 0.4, topic=f"t{i}") for i in range(20)]
    repo.get_by_user_and_course.return_value = full
    mem = {"type": "goal", "topic": "new", "content": "x", "importance": 9.0}
    await service._upsert_one("u1", "Math", mem)

    repo.delete.assert_awaited_once_with("m0")  # lowest importance == 1.0
    repo.create.assert_awaited_once()


async def test_apply_decay_evicts_memory_below_threshold(service, repo):
    stale = datetime.now(timezone.utc) - timedelta(days=400)
    repo.get_by_user_and_course.return_value = [
        _memory(id="m1", type="goal", importance=1.0, last_seen_at=stale)
    ]
    await service._apply_decay("u1", "Math")
    repo.delete.assert_awaited_once_with("m1")


async def test_apply_decay_no_change_within_ttl(service, repo):
    recent = datetime.now(timezone.utc) - timedelta(days=1)
    repo.get_by_user_and_course.return_value = [
        _memory(id="m1", type="goal", importance=5.0, last_seen_at=recent)
    ]
    await service._apply_decay("u1", "Math")
    repo.delete.assert_not_awaited()
    repo.update.assert_not_awaited()


async def test_apply_decay_updates_decayed_importance(service, repo):
    seen = datetime.now(timezone.utc) - timedelta(days=21)  # 14 days past 7-day TTL
    repo.get_by_user_and_course.return_value = [
        _memory(id="m1", type="goal", importance=8.0, last_seen_at=seen)
    ]
    await service._apply_decay("u1", "Math")
    _, updates = repo.update.call_args[0]
    assert updates["importance"] < 8.0


async def test_extract_and_upsert_swallows_llm_failure(service, repo, mocker):
    repo.get_by_user_and_course.return_value = []
    mocker.patch(
        "app.backend.services.user_memory.call_openrouter",
        side_effect=Exception("LLM down"),
    )
    await service.extract_and_upsert("u1", "Math", "conversation summary")
    repo.create.assert_not_awaited()


async def test_extract_and_upsert_noop_on_empty_response(service, repo, mocker):
    repo.get_by_user_and_course.return_value = []
    mocker.patch(
        "app.backend.services.user_memory.call_openrouter",
        return_value="",
    )
    await service.extract_and_upsert("u1", "Math", "conversation summary")
    repo.create.assert_not_awaited()


async def test_extract_and_upsert_persists_memories_from_llm_output(service, repo, mocker):
    repo.get_by_user_and_course.return_value = []
    repo.get_by_key.return_value = None
    mocker.patch(
        "app.backend.services.user_memory.call_openrouter",
        return_value='{"memories": [{"type": "goal", "topic": "exam", "content": "pass", "importance": 7}]}',
    )
    await service.extract_and_upsert("u1", "Math", "conversation summary")

    repo.create.assert_awaited_once()
    created = repo.create.call_args[0][0]
    assert created.topic == "exam"
    assert created.importance == 7.0


async def test_extract_and_upsert_continues_when_one_upsert_fails(service, repo, mocker):
    repo.get_by_user_and_course.return_value = []
    mocker.patch(
        "app.backend.services.user_memory.call_openrouter",
        return_value=(
            '{"memories": ['
            '{"type": "goal", "topic": "a", "content": "x", "importance": 5},'
            '{"type": "goal", "topic": "b", "content": "y", "importance": 6}]}'
        ),
    )
    upsert = mocker.patch.object(service, "_upsert_one", side_effect=[Exception("fail"), None])

    await service.extract_and_upsert("u1", "Math", "conversation summary")

    assert upsert.await_count == 2
