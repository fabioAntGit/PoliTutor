from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from bson import ObjectId

from app.backend.repositories.interfaces.user_memory_repository import IUserMemoryRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.gateways.interfaces.model_client import IModelClient
from app.backend.schemas.course.models import Course
from app.backend.schemas.memory.models import ExtractedMemory, MemoryExtraction, UserMemory
from app.backend.services.user_memory import UserMemoryService

USER_ID = str(ObjectId())
OTHER_USER_ID = str(ObjectId())
COURSE_ID = str(ObjectId())
COURSE_CODE = "Math"


def _memory(**kwargs) -> UserMemory:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id=str(ObjectId()),
        user_id=USER_ID,
        course_id=COURSE_ID,
        type="goal",
        topic="exam",
        content="wants to pass",
        importance=5.0,
        last_seen_at=now,
        created_at=now,
    )
    defaults.update(kwargs)
    return UserMemory(**defaults)


def _course() -> Course:
    return Course(_id=COURSE_ID, code=COURSE_CODE, name="Math", is_active=True)


@pytest.fixture
def repo():
    return AsyncMock(spec=IUserMemoryRepository)


@pytest.fixture
def model_client():
    return MagicMock(spec=IModelClient)


@pytest.fixture
def course_repo():
    repo = AsyncMock(spec=ICourseRepository)
    repo.find_by_id.return_value = _course()
    return repo


@pytest.fixture
def service(repo, model_client, course_repo):
    return UserMemoryService(repo, model_client, course_repo)


async def test_context_includes_only_important_memories(service, repo):
    repo.get_by_user_and_course.return_value = [
        _memory(importance=5.0, topic="relevant"),
        _memory(importance=1.0, topic="trivial"),
    ]
    context = await service.get_context_for_prompt(USER_ID, COURSE_ID)
    assert "relevant" in context
    assert "trivial" not in context


async def test_context_none_when_nothing_relevant(service, repo):
    repo.get_by_user_and_course.return_value = [_memory(importance=1.0)]
    assert await service.get_context_for_prompt(USER_ID, COURSE_ID) is None


async def test_list_memories_delegates_to_repo(service, repo):
    memories = [_memory(), _memory()]
    repo.get_by_user_and_course.return_value = memories
    result = await service.list_memories(USER_ID, COURSE_ID)
    assert result == memories
    repo.get_by_user_and_course.assert_awaited_once_with(USER_ID, COURSE_ID)


async def test_delete_returns_false_for_wrong_owner(service, repo):
    memory_id = str(ObjectId())
    repo.get_by_id.return_value = _memory(user_id=OTHER_USER_ID)
    assert await service.delete_memory(USER_ID, memory_id) is False
    repo.delete.assert_not_awaited()


async def test_delete_returns_false_when_not_found(service, repo):
    repo.get_by_id.return_value = None
    assert await service.delete_memory(USER_ID, str(ObjectId())) is False
    repo.delete.assert_not_awaited()


async def test_delete_succeeds_for_owner(service, repo):
    memory_id = str(ObjectId())
    repo.get_by_id.return_value = _memory(id=memory_id, user_id=USER_ID)
    assert await service.delete_memory(USER_ID, memory_id) is True
    repo.delete.assert_awaited_once_with(memory_id)


async def test_upsert_blends_importance_and_updates_content(service, repo):
    memory_id = str(ObjectId())
    repo.get_by_key.return_value = _memory(id=memory_id, importance=4.0, content="old")
    mem = ExtractedMemory(type="goal", topic="exam", content="new", importance=8.0)
    await service._upsert_one(USER_ID, COURSE_ID, mem)

    called_id, updates = repo.update.call_args[0]
    assert called_id == memory_id
    assert updates["importance"] == 6.0  # (4 + 8) / 2
    assert updates["content"] == "new"


async def test_upsert_keeps_content_when_new_less_important(service, repo):
    repo.get_by_key.return_value = _memory(importance=8.0, content="old")
    mem = ExtractedMemory(type="goal", topic="exam", content="new", importance=4.0)
    await service._upsert_one(USER_ID, COURSE_ID, mem)

    _, updates = repo.update.call_args[0]
    assert "content" not in updates


async def test_upsert_creates_new_with_normalized_topic(service, repo):
    repo.get_by_key.return_value = None
    repo.get_by_user_and_course.return_value = []
    mem = ExtractedMemory(type="goal", topic="  Final Exam ", content="pass", importance=7.0)
    await service._upsert_one(USER_ID, COURSE_ID, mem)

    created = repo.create.call_args[0][0]
    assert created.topic == "final exam"
    assert created.importance == 7.0
    assert created.user_id == USER_ID


async def test_upsert_evicts_lowest_when_cap_reached(service, repo):
    repo.get_by_key.return_value = None
    ids = [str(ObjectId()) for _ in range(20)]
    full = [_memory(id=ids[i], importance=0.5 + i * 0.4, topic=f"t{i}") for i in range(20)]
    repo.get_by_user_and_course.return_value = full
    mem = ExtractedMemory(type="goal", topic="new", content="x", importance=9.0)
    await service._upsert_one(USER_ID, COURSE_ID, mem)

    repo.delete.assert_awaited_once_with(ids[0])  # lowest importance
    repo.create.assert_awaited_once()


async def test_apply_decay_evicts_memory_below_threshold(service, repo):
    memory_id = str(ObjectId())
    stale = datetime.now(timezone.utc) - timedelta(days=400)
    repo.get_by_user_and_course.return_value = [
        _memory(id=memory_id, type="goal", importance=1.0, last_seen_at=stale)
    ]
    await service._apply_decay(USER_ID, COURSE_ID)
    repo.delete.assert_awaited_once_with(memory_id)


async def test_apply_decay_no_change_within_ttl(service, repo):
    recent = datetime.now(timezone.utc) - timedelta(days=1)
    repo.get_by_user_and_course.return_value = [
        _memory(type="goal", importance=5.0, last_seen_at=recent)
    ]
    await service._apply_decay(USER_ID, COURSE_ID)
    repo.delete.assert_not_awaited()
    repo.update.assert_not_awaited()


async def test_apply_decay_updates_decayed_importance(service, repo):
    seen = datetime.now(timezone.utc) - timedelta(days=21)  # 14 days past 7-day TTL
    repo.get_by_user_and_course.return_value = [
        _memory(type="goal", importance=8.0, last_seen_at=seen)
    ]
    await service._apply_decay(USER_ID, COURSE_ID)
    _, updates = repo.update.call_args[0]
    assert updates["importance"] < 8.0


async def test_extract_and_upsert_swallows_llm_failure(service, repo, model_client):
    repo.get_by_user_and_course.return_value = []
    model_client.call_structured.side_effect = Exception("LLM down")
    await service.extract_and_upsert(USER_ID, COURSE_ID, "conversation summary")
    repo.create.assert_not_awaited()


async def test_extract_and_upsert_noop_on_empty_response(service, repo, model_client):
    repo.get_by_user_and_course.return_value = []
    model_client.call_structured.return_value = None
    await service.extract_and_upsert(USER_ID, COURSE_ID, "conversation summary")
    repo.create.assert_not_awaited()


async def test_extract_and_upsert_persists_memories_from_llm_output(service, repo, model_client):
    repo.get_by_user_and_course.return_value = []
    repo.get_by_key.return_value = None
    model_client.call_structured.return_value = MemoryExtraction(
        memories=[ExtractedMemory(type="goal", topic="exam", content="pass", importance=7)]
    )
    await service.extract_and_upsert(USER_ID, COURSE_ID, "conversation summary")

    repo.create.assert_awaited_once()
    created = repo.create.call_args[0][0]
    assert created.topic == "exam"
    assert created.importance == 7.0


async def test_extract_and_upsert_skips_memories_with_empty_topic_or_content(service, repo, model_client):
    repo.get_by_user_and_course.return_value = []
    repo.get_by_key.return_value = None
    model_client.call_structured.return_value = MemoryExtraction(memories=[
        ExtractedMemory(type="goal", topic="", content="pass", importance=7),
        ExtractedMemory(type="goal", topic="exam", content="", importance=7),
    ])
    await service.extract_and_upsert(USER_ID, COURSE_ID, "conversation summary")
    repo.create.assert_not_awaited()


async def test_extract_and_upsert_continues_when_one_upsert_fails(service, repo, mocker, model_client):
    repo.get_by_user_and_course.return_value = []
    model_client.call_structured.return_value = MemoryExtraction(memories=[
        ExtractedMemory(type="goal", topic="a", content="x", importance=5),
        ExtractedMemory(type="goal", topic="b", content="y", importance=6),
    ])
    upsert = mocker.patch.object(service, "_upsert_one", side_effect=[Exception("fail"), None])

    await service.extract_and_upsert(USER_ID, COURSE_ID, "conversation summary")

    assert upsert.await_count == 2
