"""
Data builders for the backend integration tests.

They insert documents directly into the collections, mirroring how the app
stores them.

Dates are always **relative to `now`** (e.g. `days_ago=2`), never hardcoded, so
the tests pass on any day they happen to run.
"""

from datetime import datetime, timedelta, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _at(days_ago: float) -> datetime:
    return _now() - timedelta(days=days_ago)


async def insert_chat(
    db,
    *,
    course: str,
    user_id: str,
    summary: str | None = None,
    days_ago: float = 0,
) -> str:
    """Insert a chat and return its id as a string."""
    doc: dict = {"course": course, "user_id": user_id, "created_at": _at(days_ago)}
    if summary is not None:
        doc["summary"] = summary
    result = await db["chats"].insert_one(doc)
    return str(result.inserted_id)


async def insert_course(
    db,
    *,
    code: str,
    name: str | None = None,
    is_active: bool = True,
) -> None:
    """Insert a course (needed by the analytics auth/scope guards)."""
    await db["courses"].insert_one(
        {"code": code, "name": name or code.upper(), "description": "", "is_active": is_active}
    )


async def insert_message(
    db,
    *,
    conversation_id: str,
    role: str = "user",
    content: str = "question",
    days_ago: float = 0,
    sources: list[dict] | None = None,
) -> None:
    """Insert a message linked to a chat (via conversation_id)."""
    await db["messages"].insert_one(
        {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": _at(days_ago),
            "sources": sources or [],
        }
    )


async def insert_memory(
    db,
    *,
    mem_id: str,
    user_id: str,
    course: str,
    mem_type: str = "preference",
    topic: str = "topic",
    content: str = "content",
    importance: float = 5.0,
    last_seen_days_ago: float = 0,
) -> str:
    """Insert a user_memory document (id stored as _id) and return its id."""
    await db["user_memory"].insert_one(
        {
            "_id": mem_id,
            "user_id": user_id,
            "course": course,
            "type": mem_type,
            "topic": topic,
            "content": content,
            "importance": importance,
            "last_seen_at": _at(last_seen_days_ago),
            "created_at": _now(),
        }
    )
    return mem_id
