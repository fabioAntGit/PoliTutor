from app.backend.core.database import get_redis
from app.backend.core.config import REDIS_TTL
from app.backend.schemas.message.models import Message

class RedisRepository:
    def __init__(self) -> None:
        self.client = get_redis()
        self.ttl = REDIS_TTL

    async def add_message(self, message: Message):
        key = f"chat:{message.conversation_id}:messages"

        await self.client.rpush(key, message.model_dump_json())
        await self.client.ltrim(key, -16, -1)
        await self.increment_message_count(message.conversation_id)
        await self.refresh_session(message.conversation_id)

    async def repopulate_messages(self, conversation_id: str, messages: list[Message]):
        key = f"chat:{conversation_id}:messages"
        for msg in messages:
            await self.client.rpush(key, msg.model_dump_json())
        await self.client.ltrim(key, -16, -1)
        await self.refresh_session(conversation_id)

    async def get_messages(self, session_id: str) -> list[Message]:
        key = f"chat:{session_id}:messages"
        items = await self.client.lrange(key, 0, -1)
        return [Message.model_validate_json(item) for item in items]

    async def set_summary(self, session_id: str, summary: str):
        key = f"chat:{session_id}:summary"
        await self.client.set(key, summary)
        await self.refresh_session(session_id)

    async def get_summary(self, session_id: str) -> str | None:
        key = f"chat:{session_id}:summary"
        return await self.client.get(key)

    async def refresh_session(self, session_id: str):
        await self.client.expire(f"chat:{session_id}:messages", self.ttl)
        await self.client.expire(f"chat:{session_id}:summary", self.ttl)
        await self.client.expire(f"chat:{session_id}:message_count", self.ttl)

    async def set_message_count(self, session_id: str, count: int):
        key = f"chat:{session_id}:message_count"
        await self.client.set(key, count)
        await self.refresh_session(session_id)

    async def increment_message_count(self, session_id: str) -> int:
        key = f"chat:{session_id}:message_count"
        count = await self.client.incr(key)
        return count

    async def get_message_count(self, session_id: str) -> int:
        key = f"chat:{session_id}:message_count"
        count = await self.client.get(key)
        return int(count) if count else 0

    async def reset_message_count(self, session_id: str):
        await self.client.delete(key)

    async def get_context(self, session_id: str) -> tuple[str | None, list[Message]]:
        summary = await self.get_summary(session_id)
        messages = await self.get_messages(session_id)
        return summary, messages
