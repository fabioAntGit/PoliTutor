from datetime import datetime, timedelta, timezone

from app.backend.schemas.memory.models import UserMemory
from app.backend.services.user_memory import (
    _decayed_importance,
    _format_existing,
    _parse_extracted,
)

_TTL_7D = 7 * 24 * 3600


def _memory(**kwargs) -> UserMemory:
    now = datetime.now(timezone.utc)
    defaults = dict(
        id="mem_1",
        user_id="u1",
        course="Math",
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


def test_parse_valid_json_fenced_block():
    raw = '```json\n{"memories": [{"type": "goal", "topic": "exam", "content": "pass", "importance": 7}]}\n```'
    result = _parse_extracted(raw)
    assert len(result) == 1
    assert result[0]["topic"] == "exam"


def test_parse_invalid_json_returns_empty():
    assert _parse_extracted("this is not json") == []


def test_parse_filters_invalid_type():
    raw = '{"memories": [{"type": "bogus", "topic": "x", "content": "y", "importance": 5}]}'
    assert _parse_extracted(raw) == []


def test_parse_filters_missing_topic_or_content():
    raw = '{"memories": [{"type": "goal", "topic": "", "content": "y", "importance": 5}]}'
    assert _parse_extracted(raw) == []


def test_parse_filters_importance_out_of_range():
    raw = '{"memories": [{"type": "goal", "topic": "x", "content": "y", "importance": 11}]}'
    assert _parse_extracted(raw) == []


def test_format_existing_empty_list():
    assert _format_existing([]) == "No existing memories."


def test_format_existing_renders_fields():
    out = _format_existing([_memory(type="goal", topic="exam", content="pass")])
    assert "goal" in out
    assert "exam" in out
    assert "pass" in out
