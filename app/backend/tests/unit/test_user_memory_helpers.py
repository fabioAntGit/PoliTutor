from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.backend.schemas.memory.models import ExtractedMemory, UserMemory
from app.backend.services.user_memory import (
    _decayed_importance,
    _format_existing,
)

_TTL_7D = 7 * 24 * 3600


def _memory(**kwargs) -> UserMemory:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id="60d5ecb8b4259b3a0c4f0001",
        user_id="60d5ecb8b4259b3a0c4f0002",
        course_id="60d5ecb8b4259b3a0c4f0003",
        type="goal",
        topic="exam",
        content="wants to pass the exam",
        importance=5.0,
        last_seen_at=now,
        created_at=now,
    )
    defaults.update(kwargs)
    return UserMemory(**defaults)


def test_no_decay_within_ttl():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    last_seen = now - timedelta(days=3)
    assert _decayed_importance(5.0, last_seen, _TTL_7D, now) == 5.0


def test_decay_one_week_past_expiry():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    last_seen = now - timedelta(days=14)  # 7 days past a 7-day TTL = 1 week
    assert _decayed_importance(10.0, last_seen, _TTL_7D, now) == 8.5


def test_naive_datetime_treated_as_utc():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    naive_last_seen = (now - timedelta(days=2)).replace(tzinfo=None)
    assert _decayed_importance(5.0, naive_last_seen, _TTL_7D, now) == 5.0


def test_extracted_memory_rejects_invalid_type():
    with pytest.raises(ValidationError):
        ExtractedMemory(type="bogus", topic="x", content="y", importance=5)


def test_extracted_memory_clamps_importance_out_of_range():
    assert ExtractedMemory(type="goal", topic="x", content="y", importance=11).importance == 10.0
    assert ExtractedMemory(type="goal", topic="x", content="y", importance=-1).importance == 0.0


def test_extracted_memory_accepts_importance_boundaries():
    assert ExtractedMemory(type="goal", topic="x", content="y", importance=0).importance == 0.0
    assert ExtractedMemory(type="goal", topic="x", content="y", importance=10).importance == 10.0


def test_format_existing_empty_list():
    assert _format_existing([]) == "No existing memories."


def test_format_existing_renders_fields():
    out = _format_existing([_memory(type="goal", topic="exam", content="pass")])
    assert "goal" in out
    assert "exam" in out
    assert "pass" in out
