from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IDeletionRepository(Protocol):
    async def move_docs(self, collection: str, filter: dict[str, Any]) -> int: ...
