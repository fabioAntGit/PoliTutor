import json
from datetime import datetime, timedelta, timezone
from pymongo.asynchronous.database import AsyncDatabase
    
class AnalyticsRepository:
    def __init__(self, db: AsyncDatabase) -> None:
        self.chats = db["chats"]
        self.messages = db["messages"]

    async def get_total_conversations(self) -> int:
        return await self.chats.count_documents({})

    async def get_active_students(self) -> int:
        result = await self.chats.distinct("user_id")
        return len(result)

    async def get_total_messages(self) -> int:
        return await self.messages.count_documents({"role": "user"})

    async def get_activity(self, days: int) -> list[dict]:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        pipeline = [
            {"$match": {"role": "user", "created_at": {"$gte": start_date}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "questions": {"$sum": 1},
            }},
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 0, "date": "$_id", "questions": 1}},
        ]
        cursor = await self.messages.aggregate(pipeline)
        return await cursor.to_list(length=None)

    async def get_avg_questions_per_conversation(self) -> float:
        pipeline = [
            {"$match": {"role": "user"}},
            {"$group": {"_id": "$conversation_id", "count": {"$sum": 1}}},
            {"$group": {"_id": None, "avg": {"$avg": "$count"}}},
        ]
        cursor = await self.messages.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if not result:
            return 0.0
        return round(result[0]["avg"], 1)

    # --- Course-scoped methods ---

    async def get_courses(self) -> list[str]:
        result = await self.chats.distinct("course")
        return sorted(result)

    async def get_course_overview(self, course: str) -> dict:
        total_conversations = await self.chats.count_documents({"course": course})
        user_ids = await self.chats.distinct("user_id", {"course": course})
        conversation_ids = await self.chats.distinct("conversation_id", {"course": course})
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
        conversation_ids = await self.chats.distinct("conversation_id", {"course": course})
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
            try:
                parsed = json.loads(raw)
                concepts.extend(parsed.get("concepts_covered", []))
            except (json.JSONDecodeError, AttributeError):
                pass
        return concepts

    async def get_course_sources(self, course: str, limit: int = 10) -> list[dict]:
        conversation_ids = await self.chats.distinct("conversation_id", {"course": course})
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
