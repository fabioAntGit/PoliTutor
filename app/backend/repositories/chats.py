from bson import ObjectId
from datetime import datetime, timezone
from pymongo.asynchronous.database import AsyncDatabase
from app.backend.schemas.chat.models import Chat

class ChatRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db["chats"]

    async def create(self, chat: Chat) -> str:
        await self.collection.insert_one(chat.model_dump())
        return chat.conversation_id

    async def get_chat(self, conversation_id: str) -> Chat | None:
        document = await self.collection.find_one({"conversation_id": conversation_id})

        if document is None:
            return None
        return Chat.model_validate(document)

    async def get_chat_by_project_and_user(self, project_id: str, user_id: str) -> Chat | None:
        document = await self.collection.find_one({"project_id": project_id, "user_id": user_id})

        if document is None:
            return None
        return Chat.model_validate(document)

    async def get_chats(self, user_id: str) -> list[Chat]:
        query = self.collection.find({"user_id": user_id})
        documents = await query.to_list(length=None)
        return [Chat.model_validate(document) for document in documents]

    async def get_summary(self, conversation_id: str) -> str | None:
        document = await self.collection.find_one(
            {"conversation_id": conversation_id},
            {"summary": 1, "_id": 0}
        )
        return document.get("summary") if document else None

    async def set_summary(self, conversation_id: str, summary: str, last_message_id: str):
        await self.collection.update_one(
            {"conversation_id": conversation_id},
            {
                "$set": {
                    "summary": summary,
                    "last_summarized_message_id": ObjectId(last_message_id),
                    "updated_at": datetime.now(timezone.utc)
                }
            }
        )
    
    async def get_last_summarized_message_id(self, conversation_id: str) -> str | None:
        document = await self.collection.find_one(
            {"conversation_id": conversation_id},
            {"last_summarized_message_id": 1, "_id": 0}
        )
        res = document.get("last_summarized_message_id") if document else None
        return str(res) if res else None
