from bson import ObjectId
from app.backend.core.database import get_db
from app.backend.schemas.message.models import Message

class MessageRepository:
    def __init__(self) -> None:
        self.collection = get_db()["messages"]

    async def create(self, message: Message) -> str:
        data = message.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(data)
        message.id = str(result.inserted_id)
        return message.conversation_id

    async def get_message(self, message_id: str) -> Message | None:
        document = await self.collection.find_one({"_id": ObjectId(message_id)})
        return Message.model_validate(document) if document else None

    async def get_next_message(self, message_id: str, conversation_id: str) -> Message | None:
        query = {
            "conversation_id": conversation_id,
            "_id": {"$gt": ObjectId(message_id)}
        }
        document = await self.collection.find_one(query, sort=[("_id", 1)])
        return Message.model_validate(document) if document else None

    async def get_messages(self, conversation_id: str) -> list[Message]:
        query = self.collection.find({"conversation_id": conversation_id}).sort("_id", 1)
        documents = await query.to_list(length=None)
        return [Message.model_validate(document) for document in documents]

    async def get_recent_messages(self, conversation_id: str, limit: int = 16) -> list[Message]:
        query = self.collection.find({"conversation_id": conversation_id}).sort("_id", -1)
        documents = await query.to_list(length=limit)
        documents.reverse()
        return [Message.model_validate(document) for document in documents]

    async def get_number_of_messages_after_summary(self, conversation_id: str, last_summarized_message_id: str | None) -> int:
        if not last_summarized_message_id:
            return await self.collection.count_documents({"conversation_id": conversation_id})

        query_filter = {
            "conversation_id": conversation_id,
            "_id": {"$gt": ObjectId(last_summarized_message_id)}
        }
        return await self.collection.count_documents(query_filter)

    async def update_report_status(self, message_id: str, is_reported: bool) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"is_reported": is_reported}}
        )
        return result.modified_count > 0