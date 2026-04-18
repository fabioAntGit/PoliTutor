from app.backend.core.database import get_db
from app.backend.schemas.chat.models import Chat

class ChatRepository:
    def __init__(self) -> None:
        self.collection = get_db()["chats"]

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
