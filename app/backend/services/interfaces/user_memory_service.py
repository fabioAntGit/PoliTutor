from typing import Protocol, runtime_checkable

from app.backend.schemas.memory.models import UserMemory


@runtime_checkable
class IUserMemoryService(Protocol):
    async def extract_and_upsert(self, user_id: str, course: str, summary: str) -> None: ...

    async def get_context_for_prompt(self, user_id: str, course: str) -> str | None: ...

    async def list_memories(self, user_id: str, course: str) -> list[UserMemory]: ...

    async def delete_memory(self, user_id: str, mem_id: str) -> bool: ...
