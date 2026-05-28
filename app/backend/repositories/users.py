from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase
from app.backend.schemas.user.models import User

from app.backend.repositories.interfaces.user_repository import IUserRepository

class UserRepository(IUserRepository):
    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db["users"]

    async def create(self, user: User) -> bool:
        result = await self.collection.insert_one(user.model_dump(exclude={"id"}, by_alias=False))
        return result.acknowledged
        
    async def find_by_email(self, email: str) -> User | None: 
        result = await self.collection.find_one({"email": email})
        return User.model_validate(result) if result else None
    
    async def find_by_username(self, username: str) -> User | None: 
        result = await self.collection.find_one({"username": username})
        return User.model_validate(result) if result else None
        
    async def find_all(self) -> list[User]:
        users = []
        async for user in self.collection.find({"is_active": True}):
            users.append(User.model_validate(user))
        return users

    async def update(self, username: str, fields: dict) -> bool: 
        result = await self.collection.update_one(
            {"username": username}, 
            {"$set": fields}
        )
        return result.modified_count > 0
    
    async def delete(self, username: str) -> bool: 
        result = await self.collection.update_one(
            {"username": username}, 
            {"$set": {"is_active": False}}
        )
        return result.modified_count > 0
