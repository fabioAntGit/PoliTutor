from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from app.backend.schemas.memory.models import MemoryType, UserMemory
from app.backend.repositories.interfaces.user_memory_repository import IUserMemoryRepository


class UserMemoryRepository(IUserMemoryRepository):
    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db["user_memory"]

    async def create(self, memory: UserMemory) -> None:
        # Honor an explicit _id when provided; otherwise let Mongo generate one.
        await self.collection.insert_one(memory.model_dump(by_alias=True, exclude_none=True))

    async def update(self, memory_id: str, fields: dict) -> None:
        await self.collection.update_one({"_id": ObjectId(memory_id)}, {"$set": fields})

    async def delete(self, memory_id: str) -> None:
        await self.collection.delete_one({"_id": ObjectId(memory_id)})

    async def get_by_id(self, memory_id: str) -> UserMemory | None:
        doc = await self.collection.find_one({"_id": ObjectId(memory_id)})
        return UserMemory.model_validate(doc) if doc else None

    async def get_by_key(self, user_id: str, course_id: str, type: MemoryType, topic: str) -> UserMemory | None:
        doc = await self.collection.find_one({
            "user_id": ObjectId(user_id),
            "course_id": ObjectId(course_id),
            "type": type,
            "topic": topic,
        })
        return UserMemory.model_validate(doc) if doc else None

    async def get_by_user_and_course(self, user_id: str, course_id: str) -> list[UserMemory]:
        cursor = self.collection.find({"user_id": ObjectId(user_id), "course_id": ObjectId(course_id)})
        return [UserMemory.model_validate(d) for d in await cursor.to_list(length=None)]
