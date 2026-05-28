import logging
from datetime import datetime, timezone
from typing import Any

from pymongo.asynchronous.database import AsyncDatabase

from app.backend.repositories.interfaces.deletion_repository import IDeletionRepository

logger = logging.getLogger(__name__)


class DeletionRepository(IDeletionRepository):
    def __init__(self, db_main: AsyncDatabase, db_deprecated: AsyncDatabase) -> None:
        self.db_main = db_main
        self.db_deprecated = db_deprecated

    async def move_docs(self, collection: str, filter: dict[str, Any]) -> int:
        source = self.db_main[collection]
        target = self.db_deprecated[collection]

        cursor = source.find(filter)
        docs = await cursor.to_list(length=None)

        if not docs:
            return 0

        now = datetime.now(timezone.utc)
        for doc in docs:
            doc["deleted_at"] = now

        await target.insert_many(docs)
        result = await source.delete_many(filter)

        logger.info(
            "Moved %d doc(s) from %s to %s_deprecated",
            result.deleted_count,
            collection,
            collection,
        )
        return result.deleted_count
