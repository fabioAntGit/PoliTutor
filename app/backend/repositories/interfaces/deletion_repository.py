from typing import Protocol, runtime_checkable


@runtime_checkable
class IDeletionRepository(Protocol):
    async def move_user_related_docs(
        self,
        *,
        user_id: str,
        username: str,
        conversation_ids: list[str],
    ) -> None: ...
