from bson import ObjectId
from app.backend.core.database import get_db
from app.backend.schemas.report.models import Report

class ReportRepository:
    def __init__(self) -> None:
        self.collection = get_db()["reports"]

    async def create(self, report: Report) -> bool:
        result = await self.collection.insert_one(report.model_dump(by_alias=True))
        return result.acknowledged

    async def exists_by_message_id(self, message_id: str) -> bool:
        count = await self.collection.count_documents({"message_id": message_id})
        return count > 0

    async def delete_by_message_id(self, message_id: str) -> bool:
        result = await self.collection.delete_many({"message_id": message_id})
        return result.deleted_count > 0