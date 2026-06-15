from typing import Protocol, runtime_checkable

@runtime_checkable
class IContextService(Protocol):
    async def get_or_load_context(self, conversation_id: str) -> tuple[str | None, list[dict]]:
        ...

    async def check_and_trigger_summary(self, conversation_id: str, user_id: str, course: str) -> None:
        ...
