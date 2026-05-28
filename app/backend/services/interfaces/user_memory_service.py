from abc import ABC, abstractmethod

from app.backend.schemas.memory.models import UserMemory


class IUserMemoryService(ABC):
    @abstractmethod
    async def extract_and_upsert(self, user_id: str, course: str, summary: str) -> None: ...

    @abstractmethod
    async def get_context_for_prompt(self, user_id: str, course: str) -> str | None: ...

    @abstractmethod
    async def list_memories(self, user_id: str, course: str) -> list[UserMemory]: ...

    @abstractmethod
    async def delete_memory(self, user_id: str, mem_id: str) -> bool: ...
