import asyncio
import logging
from datetime import datetime, timezone

from app.backend.repositories.interfaces.user_memory_repository import IUserMemoryRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.schemas.memory.models import ExtractedMemory, MemoryExtraction, UserMemory
from app.backend.services.interfaces.user_memory_service import IUserMemoryService
from app.backend.gateways.interfaces.model_client import IModelClient
from app.backend.core.config import (
    MAX_MEMORIES_PER_COURSE,
    MEMORY_DECAY_RATE_PER_WEEK,
    MEMORY_DELETE_IMPORTANCE_THRESHOLD,
    MEMORY_EXTRACTION_PROMPT,
    MEMORY_MIN_IMPORTANCE_FOR_INJECTION,
    MEMORY_TTL_BY_TYPE,
    OPENROUTER_MODEL_MEMORY_EXTRACTION,
)

logger = logging.getLogger(__name__)


def _decayed_importance(importance: float, last_seen_at: datetime, ttl: int, now: datetime) -> float:
    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)
    elapsed = (now - last_seen_at).total_seconds()
    if elapsed <= ttl:
        return round(importance, 3)
    weeks_since_expiry = (elapsed - ttl) / (7 * 24 * 3600)
    return round(importance * ((1 - MEMORY_DECAY_RATE_PER_WEEK) ** weeks_since_expiry), 3)


def _format_existing(memories: list[UserMemory]) -> str:
    if not memories:
        return "No existing memories."
    return "\n".join(
        f"- {m.type} | {m.topic}: {m.content} (importance: {m.importance}/10)"
        for m in memories
    )


class UserMemoryService(IUserMemoryService):
    def __init__(
        self,
        repo: IUserMemoryRepository,
        model_client: IModelClient,
        course_repository: ICourseRepository,
    ) -> None:
        self.repo = repo
        self.model_client = model_client
        self.course_repository = course_repository

    async def extract_and_upsert(self, user_id: str, course_id: str, summary: str) -> None:
        course = await self.course_repository.find_by_id(course_id)
        if course is None:
            logger.warning("Skipping memory extraction: unknown course '%s'", course_id)
            return

        await self._apply_decay(user_id, course_id)

        existing = await self.repo.get_by_user_and_course(user_id, course_id)

        prompt = MEMORY_EXTRACTION_PROMPT.format(
            course=course.name,
            summary=summary,
            existing_memories=_format_existing(existing),
        )

        try:
            extraction = await asyncio.to_thread(
                self.model_client.call_structured,
                [{"role": "user", "content": prompt}],
                MemoryExtraction,
                model=OPENROUTER_MODEL_MEMORY_EXTRACTION,
                max_tokens=600,
                temperature=0.1,
            )
        except Exception as e:
            logger.error("Memory extraction LLM call failed for user %s: %s", user_id, e)
            return

        if extraction is None:
            return

        extracted = [m for m in extraction.memories if m.topic and m.content]
        logger.info("Extracted %d memories for user %s / course %s", len(extracted), user_id, course_id)

        for mem in extracted:
            try:
                await self._upsert_one(user_id, course_id, mem)
            except Exception as e:
                logger.error("Failed to upsert memory for user %s, topic '%s': %s", user_id, mem.topic, e)

    async def get_context_for_prompt(self, user_id: str, course_id: str) -> str | None:
        memories = await self.repo.get_by_user_and_course(user_id, course_id)
        relevant = [m for m in memories if m.importance >= MEMORY_MIN_IMPORTANCE_FOR_INJECTION]
        if not relevant:
            return None
        lines = [f"• {m.type} | {m.topic}: {m.content}" for m in relevant]
        return "[Student Memory]\n" + "\n".join(lines)

    async def list_memories(self, user_id: str, course_id: str) -> list[UserMemory]:
        return await self.repo.get_by_user_and_course(user_id, course_id)

    async def delete_memory(self, user_id: str, mem_id: str) -> bool:
        memory = await self.repo.get_by_id(mem_id)
        if not memory or memory.user_id != user_id:
            return False
        await self.repo.delete(mem_id)
        logger.info("Deleted memory %s for user %s", mem_id, user_id)
        return True

    async def _apply_decay(self, user_id: str, course_id: str) -> None:
        memories = await self.repo.get_by_user_and_course(user_id, course_id)
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

    async def _upsert_one(self, user_id: str, course_id: str, mem: ExtractedMemory) -> None:
        topic = mem.topic.strip().lower()
        content = mem.content
        new_importance = round(mem.importance, 2)

        now = datetime.now(timezone.utc)
        existing = await self.repo.get_by_key(user_id, course_id, mem.type, topic)

        if existing:
            blended = round(min((existing.importance + new_importance) / 2, 10.0), 2)
            updates: dict = {"importance": blended, "last_seen_at": now}
            if new_importance > existing.importance:
                updates["content"] = content
            await self.repo.update(existing.id, updates)
            logger.debug("Updated memory %s (topic: %s, %.2f → %.2f)", existing.id, topic, existing.importance, blended)
        else:
            all_memories = await self.repo.get_by_user_and_course(user_id, course_id)
            if len(all_memories) >= MAX_MEMORIES_PER_COURSE:
                lowest = min(all_memories, key=lambda m: m.importance)
                await self.repo.delete(lowest.id)
                logger.info("Cap reached (%d), evicted memory %s (topic: %s, importance: %.2f)", MAX_MEMORIES_PER_COURSE, lowest.id, lowest.topic, lowest.importance)

            new_mem = UserMemory(
                user_id=user_id,
                course_id=course_id,
                type=mem.type,
                topic=topic,
                content=content,
                importance=new_importance,
                last_seen_at=now,
                created_at=now,
            )
            await self.repo.create(new_mem)
            logger.debug("Created memory (topic: %s, importance: %.2f)", topic, new_importance)
