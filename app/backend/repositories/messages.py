from app.backend.core.database import get_db
from app.backend.schemas.message.models import Message

class MessageRepository:
    def __init__(self) -> None:
        self.collection = get_db()["messages"]

    async def create(self, message: Message) -> str:
        await self.collection.insert_one(message.model_dump())
        return message.conversation_id

    async def get_messages(self, conversation_id: str) -> list[Message]:
        query = self.collection.find({"conversation_id": conversation_id})
        documents = await query.to_list(length=None)
        return [Message.model_validate(document) for document in documents]
