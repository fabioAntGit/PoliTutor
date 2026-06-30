"""Mongo document builders for integration tests (all ids are ObjectId hex strings)."""
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from pwdlib import PasswordHash

_password_hash = PasswordHash.recommended()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _at(days_ago: float) -> datetime:
    return _now() - timedelta(days=days_ago)


async def insert_chat(
    db,
    *,
    course_id: str,
    user_id: str,
    summary: str | None = None,
    days_ago: float = 0,
) -> str:
    """Insert a chat and return its id as a string."""
    doc: dict = {
        "course_id": ObjectId(course_id),
        "user_id": ObjectId(user_id),
        "created_at": _at(days_ago),
    }
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
) -> str:
    """Insert a course and return its id as a string."""
    result = await db["courses"].insert_one(
        {"code": code, "name": name or code.upper(), "description": "", "is_active": is_active}
    )
    return str(result.inserted_id)


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
            "conversation_id": ObjectId(conversation_id),
            "role": role,
            "content": content,
            "created_at": _at(days_ago),
            "sources": sources or [],
        }
    )


async def insert_user(
    db,
    *,
    username: str,
    password: str = "password123",
    email: str | None = None,
    full_name: str = "Test User",
    role: str = "student",
    courses: list[str] | None = None,
    must_change_password: bool = False,
) -> str:
    """Insert a user with a real password hash and return its id as a string.

    `courses` are course ObjectId hex strings (create them with `insert_course`).
    """
    course_ids = [ObjectId(c) for c in (courses or [])]
    user_id = ObjectId()
    await db["users"].insert_one(
        {
            "_id": user_id,
            "email": email or f"{username}@estg.ipp.pt",
            "username": username,
            "role": role,
            "hashed_password": _password_hash.hash(password),
            "full_name": full_name,
            "courses": course_ids,
            "must_change_password": must_change_password,
            "created_at": _now(),
            "updated_at": _now(),
        }
    )
    return str(user_id)


async def insert_memory(
    db,
    *,
    user_id: str,
    course_id: str,
    mem_id: str | None = None,
    mem_type: str = "preference",
    topic: str = "topic",
    content: str = "content",
    importance: float = 5.0,
    last_seen_days_ago: float = 0,
) -> str:
    """Insert a user_memory document and return its id as a string."""
    doc: dict = {
        "user_id": ObjectId(user_id),
        "course_id": ObjectId(course_id),
        "type": mem_type,
        "topic": topic,
        "content": content,
        "importance": importance,
        "last_seen_at": _at(last_seen_days_ago),
        "created_at": _now(),
    }
    if mem_id is not None:
        doc["_id"] = ObjectId(mem_id)
    result = await db["user_memory"].insert_one(doc)
    return str(result.inserted_id)
