import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from uuid import uuid4

from app.backend.repositories.interfaces.user_memory_repository import IUserMemoryRepository
from app.backend.schemas.memory.models import MemoryType, UserMemory
from app.backend.services.interfaces.user_memory_service import IUserMemoryService
from rag.src.shared.call_model import call_openrouter
from rag.src.shared.config import (
    MAX_MEMORIES_PER_COURSE,
    MEMORY_DECAY_RATE_PER_WEEK,
    MEMORY_DELETE_IMPORTANCE_THRESHOLD,
    MEMORY_EXTRACTION_PROMPT,
    MEMORY_MIN_IMPORTANCE_FOR_INJECTION,
    MEMORY_TTL_BY_TYPE,
    OPENROUTER_MODEL_MEMORY_EXTRACTION,
)

logger = logging.getLogger(__name__)

_JSON_BLOCK = re.compile(r"```json\s*(.*?)\s*```", re.DOTALL)
_VALID_TYPES: set[str] = {"difficulty", "preference", "goal", "progress"}


def _decayed_importance(importance: float, last_seen_at: datetime, ttl: int, now: datetime) -> float:
    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)
    elapsed = (now - last_seen_at).total_seconds()
    if elapsed <= ttl:
        return round(importance, 3)
    weeks_since_expiry = (elapsed - ttl) / (7 * 24 * 3600)
    return round(importance * ((1 - MEMORY_DECAY_RATE_PER_WEEK) ** weeks_since_expiry), 3)


def _parse_extracted(raw: str) -> list[dict]:
    text = raw.strip()
    match = _JSON_BLOCK.search(text)
    if match:
        text = match.group(1)
    try:
        data = json.loads(text)
        return [
            m for m in data.get("memories", [])
            if isinstance(m, dict)
            and m.get("type") in _VALID_TYPES
            and m.get("topic")
            and m.get("content")
            and 0.0 <= float(m.get("importance", -1)) <= 10.0
        ]
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse memory extraction response")
        return []


def _format_existing(memories: list[UserMemory]) -> str:
    if not memories:
        return "No existing memories."
    return "\n".join(
        f"- {m.type} | {m.topic}: {m.content} (importance: {m.importance}/10)"
        for m in memories
    )


class UserMemoryService(IUserMemoryService):
    def __init__(self, repo: IUserMemoryRepository) -> None:
        self.repo = repo

    async def extract_and_upsert(self, user_id: str, course: str, summary: str) -> None:
        await self._apply_decay(user_id, course)

        existing = await self.repo.get_by_user_and_course(user_id, course)

        prompt = MEMORY_EXTRACTION_PROMPT.format(
            course=course,
            summary=summary,
            existing_memories=_format_existing(existing),
        )

        try:
            raw = await asyncio.to_thread(
                call_openrouter,
                prompt,
                model=OPENROUTER_MODEL_MEMORY_EXTRACTION,
                max_tokens=600,
                temperature=0.1,
            )
        except Exception as e:
            logger.error("Memory extraction LLM call failed for user %s: %s", user_id, e)
            return

        if not raw:
            return

        extracted = _parse_extracted(raw)
        logger.info("Extracted %d memories for user %s / course %s", len(extracted), user_id, course)

        for mem in extracted:
            try:
                await self._upsert_one(user_id, course, mem)
            except Exception as e:
                logger.error("Failed to upsert memory for user %s, topic '%s': %s", user_id, mem.get("topic"), e)

    async def get_context_for_prompt(self, user_id: str, course: str) -> str | None:
        memories = await self.repo.get_by_user_and_course(user_id, course)
        relevant = [m for m in memories if m.importance >= MEMORY_MIN_IMPORTANCE_FOR_INJECTION]
        if not relevant:
            return None
        lines = [f"• {m.type} | {m.topic}: {m.content}" for m in relevant]
        return "[Student Memory]\n" + "\n".join(lines)

    async def list_memories(self, user_id: str, course: str) -> list[UserMemory]:
        return await self.repo.get_by_user_and_course(user_id, course)

    async def delete_memory(self, user_id: str, mem_id: str) -> bool:
        memory = await self.repo.get_by_id(mem_id)
        if not memory or memory.user_id != user_id:
            return False
        await self.repo.delete(mem_id)
        logger.info("Deleted memory %s for user %s", mem_id, user_id)
        return True

    async def _apply_decay(self, user_id: str, course: str) -> None:
        memories = await self.repo.get_by_user_and_course(user_id, course)
        now = datetime.now(timezone.utc)

        for memory in memories:
            ttl = MEMORY_TTL_BY_TYPE[memory.type]
            decayed = _decayed_importance(memory.importance, memory.last_seen_at, ttl, now)

            if decayed < MEMORY_DELETE_IMPORTANCE_THRESHOLD:
                await self.repo.delete(memory.id)
                logger.debug("Evicted decayed memory %s (topic: %s, %.2f → %.2f)", memory.id, memory.topic, memory.importance, decayed)
            elif decayed < memory.importance - 0.01:
                await self.repo.update(memory.id, {"importance": decayed})
                logger.debug("Decayed memory %s (topic: %s, %.2f → %.2f)", memory.id, memory.topic, memory.importance, decayed)

    async def _upsert_one(self, user_id: str, course: str, mem: dict) -> None:
        mem_type: MemoryType = mem["type"]
        topic: str = mem["topic"].strip().lower()
        content: str = mem["content"]
        new_importance: float = round(float(mem["importance"]), 2)

        now = datetime.now(timezone.utc)
        existing = await self.repo.get_by_key(user_id, course, mem_type, topic)

        if existing:
            blended = round(min((existing.importance + new_importance) / 2, 10.0), 2)
            updates: dict = {"importance": blended, "last_seen_at": now}
            if new_importance > existing.importance:
                updates["content"] = content
            await self.repo.update(existing.id, updates)
            logger.debug("Updated memory %s (topic: %s, %.2f → %.2f)", existing.id, topic, existing.importance, blended)
        else:
            all_memories = await self.repo.get_by_user_and_course(user_id, course)
            if len(all_memories) >= MAX_MEMORIES_PER_COURSE:
                lowest = min(all_memories, key=lambda m: m.importance)
                await self.repo.delete(lowest.id)
                logger.info("Cap reached (%d), evicted memory %s (topic: %s, importance: %.2f)", MAX_MEMORIES_PER_COURSE, lowest.id, lowest.topic, lowest.importance)

            new_mem = UserMemory(
                id=f"mem_{uuid4().hex[:16]}",
                user_id=user_id,
                course=course,
                type=mem_type,
                topic=topic,
                content=content,
                importance=new_importance,
                last_seen_at=now,
                created_at=now,
            )
            await self.repo.create(new_mem)
            logger.debug("Created memory %s (topic: %s, importance: %.2f)", new_mem.id, topic, new_importance)
