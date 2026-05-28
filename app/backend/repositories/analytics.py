import json
from datetime import datetime, timedelta, timezone
from pymongo.asynchronous.database import AsyncDatabase
import re

from app.backend.repositories.interfaces.analytics_repository import IAnalyticsRepository


def _course_match(course_filter: list[str] | None) -> dict:
    if course_filter is None:
        return {}
    return {"course": {"$in": course_filter}}


class AnalyticsRepository(IAnalyticsRepository):
    def __init__(self, db: AsyncDatabase) -> None:
        self.chats = db["chats"]
        self.messages = db["messages"]

    async def _scoped_conversation_ids(self, course_filter: list[str] | None) -> list[str] | None:
        """Returns None when no filter; otherwise list of conversation ids for the given courses."""
        if course_filter is None:
            return None
        if not course_filter:
            return []
        ids = await self.chats.distinct("_id", {"course": {"$in": course_filter}})
        return [str(cid) for cid in ids]

    async def get_total_conversations(self, course_filter: list[str] | None = None) -> int:
        return await self.chats.count_documents(_course_match(course_filter))

    async def get_active_students(self, course_filter: list[str] | None = None) -> int:
        if course_filter is None:
            result = await self.chats.distinct("user_id")
        else:
            if not course_filter:
                return 0
            result = await self.chats.distinct("user_id", {"course": {"$in": course_filter}})
        return len(result)

    async def get_total_messages(self, course_filter: list[str] | None = None) -> int:
        match: dict = {"role": "user"}
        if course_filter is not None:
            conversation_ids = await self._scoped_conversation_ids(course_filter)
            if not conversation_ids:
                return 0
            match["conversation_id"] = {"$in": conversation_ids}
        return await self.messages.count_documents(match)

    async def get_activity(self, days: int, course_filter: list[str] | None = None) -> list[dict]:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        match: dict = {"role": "user", "created_at": {"$gte": start_date}}
        if course_filter is not None:
            conversation_ids = await self._scoped_conversation_ids(course_filter)
            if not conversation_ids:
                return []
            match["conversation_id"] = {"$in": conversation_ids}
        pipeline = [
            {"$match": match},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "questions": {"$sum": 1},
            }},
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 0, "date": "$_id", "questions": 1}},
        ]
        cursor = await self.messages.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_avg_questions_per_conversation(self, course_filter: list[str] | None = None) -> float:
        match: dict = {"role": "user"}
        if course_filter is not None:
            conversation_ids = await self._scoped_conversation_ids(course_filter)
            if not conversation_ids:
                return 0.0
            match["conversation_id"] = {"$in": conversation_ids}
        pipeline = [
            {"$match": match},
            {"$group": {"_id": "$conversation_id", "count": {"$sum": 1}}},
            {"$group": {"_id": None, "avg": {"$avg": "$count"}}},
        ]
        cursor = await self.messages.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if not result:
            return 0.0
        return round(result[0]["avg"], 1)

    # --- Course-scoped methods ---

    async def get_courses(self, course_filter: list[str] | None = None) -> list[str]:
        if course_filter is None:
            result = await self.chats.distinct("course")
        else:
            if not course_filter:
                return []
            result = await self.chats.distinct("course", {"course": {"$in": course_filter}})
        return sorted(result)

    async def get_course_overview(self, course: str) -> dict:
        total_conversations = await self.chats.count_documents({"course": course})
        user_ids = await self.chats.distinct("user_id", {"course": course})
        conversation_ids = [str(cid) for cid in await self.chats.distinct("_id", {"course": course})]
        total_messages = await self.messages.count_documents({
            "conversation_id": {"$in": conversation_ids},
            "role": "user",
        })
        avg = round(total_messages / total_conversations, 1) if total_conversations else 0.0
        return {
            "total_conversations": total_conversations,
            "active_students": len(user_ids),
            "total_messages": total_messages,
            "avg_questions_per_conversation": avg,
        }

    async def get_course_activity(self, course: str, days: int) -> list[dict]:
        conversation_ids = [str(cid) for cid in await self.chats.distinct("_id", {"course": course})]
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        pipeline = [
            {"$match": {
                "role": "user",
                "conversation_id": {"$in": conversation_ids},
                "created_at": {"$gte": start_date},
            }},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "questions": {"$sum": 1},
            }},
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 0, "date": "$_id", "questions": 1}},
        ]
        cursor = await self.messages.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_course_concepts(self, course: str) -> list[str]:
        cursor = self.chats.find(
            {"course": course, "summary": {"$exists": True, "$nin": [None, ""]}},
            {"summary": 1, "_id": 0},
        )
        docs = await cursor.to_list(length=None)

        concepts: list[str] = []

        for doc in docs:
            raw = doc.get("summary", "")

            if not isinstance(raw, str):
                continue

            cleaned = re.sub(r"^```json\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)

            try:
                parsed = json.loads(cleaned)

                tags = parsed.get("concept_tags")

                if tags and isinstance(tags, list):
                    concepts.extend(tags)
                else:
                    concepts.extend(parsed.get("concepts_covered", []))

            except json.JSONDecodeError:
                continue

        return concepts

    async def get_course_sources(self, course: str, limit: int = 10) -> list[dict]:
        conversation_ids = [str(cid) for cid in await self.chats.distinct("_id", {"course": course})]
        pipeline = [
            {"$match": {"conversation_id": {"$in": conversation_ids}, "role": "assistant"}},
            {"$unwind": "$sources"},
            {"$group": {"_id": "$sources.filename", "references": {"$sum": 1}}},
            {"$sort": {"references": -1}},
            {"$limit": limit},
            {"$project": {"_id": 0, "filename": "$_id", "references": 1}},
        ]
        cursor = await self.messages.aggregate(pipeline)
        return await cursor.to_list(length=None)
