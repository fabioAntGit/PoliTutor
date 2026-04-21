from typing import Protocol, runtime_checkable
from app.backend.schemas.message.models import Message

@runtime_checkable
class IContextService(Protocol):
    async def get_or_load_context(self, conversation_id: str) -> tuple[str | None, str]:
        ...

    async def check_and_trigger_summary(
        self, 
        conversation_id: str,
        iaedu_url: str | None = None,
        iaedu_channel_id: str | None = None,
        iaedu_api_key: str | None = None,
    ) -> None:
        ...
