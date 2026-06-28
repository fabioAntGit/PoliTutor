import redis.asyncio as redis
from app.backend.core.config import REDIS_TTL, SUMMARY_LOCK_TTL
from app.backend.schemas.message.models import Message

from app.backend.repositories.interfaces.cache_repository import ICacheRepository

class RedisRepository(ICacheRepository):
    def __init__(self, client: redis.Redis) -> None:
        self.client = client
        self.ttl = REDIS_TTL
        self.summary_lock_ttl = SUMMARY_LOCK_TTL

    async def add_message(self, message: Message):
        key = f"chat:{message.conversation_id}:messages"

        await self.client.rpush(key, message.model_dump_json())
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

    async def acquire_summary_lock(self, session_id: str) -> bool:
        key = f"chat:{session_id}:lock_summary"
        return bool(await self.client.set(key, "1", ex=self.summary_lock_ttl, nx=True))

    async def release_summary_lock(self, session_id: str) -> None:
        key = f"chat:{session_id}:lock_summary"
        await self.client.delete(key)

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
        key = f"chat:{session_id}:message_count"
        await self.client.delete(key)

    async def trim_messages(self, session_id: str, limit: int = 16) -> None:
        key = f"chat:{session_id}:messages"
        await self.client.ltrim(key, -limit, -1)
        await self.refresh_session(session_id)

    async def get_context(self, session_id: str) -> tuple[str | None, list[Message]]:
        summary = await self.get_summary(session_id)
        messages = await self.get_messages(session_id)
        return summary, messages

    async def add_token_to_blacklist(self, token: str, expire_in_seconds: int) -> None:
        key = f"blacklist:{token}"
        await self.client.set(key, "revoked", ex=expire_in_seconds)

    async def is_token_blacklisted(self, token: str) -> bool:
        key = f"blacklist:{token}"
        return await self.client.exists(key) > 0
