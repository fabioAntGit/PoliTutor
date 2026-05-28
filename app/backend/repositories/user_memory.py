from pymongo.asynchronous.database import AsyncDatabase

from app.backend.schemas.memory.models import MemoryType, UserMemory
from app.backend.repositories.interfaces.user_memory_repository import IUserMemoryRepository


class UserMemoryRepository(IUserMemoryRepository):
    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db["user_memory"]

    @staticmethod
    def _from_doc(doc: dict) -> UserMemory:
        doc["id"] = doc.pop("_id")
        return UserMemory(**doc)

    async def create(self, memory: UserMemory) -> None:
        doc = memory.model_dump()
        doc["_id"] = doc.pop("id")
        await self.collection.insert_one(doc)

    async def update(self, memory_id: str, fields: dict) -> None:
        await self.collection.update_one({"_id": memory_id}, {"$set": fields})

    async def delete(self, memory_id: str) -> None:
        await self.collection.delete_one({"_id": memory_id})

    async def get_by_id(self, memory_id: str) -> UserMemory | None:
        doc = await self.collection.find_one({"_id": memory_id})
        return self._from_doc(doc) if doc else None

    async def get_by_key(self, user_id: str, course: str, type: MemoryType, topic: str) -> UserMemory | None:
        doc = await self.collection.find_one({
            "user_id": user_id,
            "course": course,
            "type": type,
            "topic": topic,
        })
        return self._from_doc(doc) if doc else None

    async def get_by_user_and_course(self, user_id: str, course: str) -> list[UserMemory]:
        cursor = self.collection.find({"user_id": user_id, "course": course})
        return [self._from_doc(d) for d in await cursor.to_list(length=None)]
