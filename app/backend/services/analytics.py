from collections import Counter
from datetime import date, timedelta
from typing import Literal

from app.backend.core.exceptions import AccessDeniedError, NotFoundError
from app.backend.repositories.interfaces.analytics_repository import IAnalyticsRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.schemas.user.enums import UserRole
from app.backend.services.interfaces.analytics_service import IAnalyticsService

_DAYS_MAP = {"7d": 7, "30d": 30, "90d": 90}


def _fill_activity_dates(raw: list[dict], days: int) -> list[dict]:
    counts = {item["date"]: item["questions"] for item in raw}
    today = date.today()
    start = today - timedelta(days=days - 1)

    data = []
    current = start

    while current <= today:
        date_str = current.strftime("%Y-%m-%d")
        data.append({"date": date_str, "questions": counts.get(date_str, 0)})
        current += timedelta(days=1)

    return data
    

class AnalyticsService(IAnalyticsService):
    def __init__(
        self,
        analytics_repository: IAnalyticsRepository,
        course_repository: ICourseRepository,
        user_repository: IUserRepository,
    ) -> None:
        self.repo = analytics_repository
        self.course_repository = course_repository
        self.user_repository = user_repository

    async def resolve_filter_scope(self, payload: dict) -> list[str]:
        active = await self.course_repository.get_active_courses()
        if payload.get("role") == UserRole.ADMIN.value:
            return sorted(c.id for c in active)
        user = await self.user_repository.find_by_id(payload.get("id", ""))
        if user is None:
            return []
        active_ids = {c.id for c in active}
        return sorted(cid for cid in user.courses if cid in active_ids)

    async def resolve_course_scope(self, course_id: str, payload: dict) -> str:
        found = await self.course_repository.find_by_id(course_id)
        if found is None or not found.is_active:
            raise NotFoundError(
                message="Cadeira nao encontrada",
                code="course_not_found",
                details={"course_id": course_id},
            )
        if payload.get("role") != UserRole.ADMIN.value:
            user = await self.user_repository.find_by_id(payload.get("id", ""))
            if user is None or found.id not in user.courses:
                raise AccessDeniedError(message="Nao tens acesso a esta cadeira.")
        return course_id

    async def get_activity(
        self,
        range_param: Literal["7d", "30d", "90d"],
        course_filter: list[str] | None = None,
    ) -> list[dict]:
        days = _DAYS_MAP[range_param]
        raw = await self.repo.get_activity(days, course_filter=course_filter)
        return _fill_activity_dates(raw, days)

    async def get_overview(self, course_filter: list[str] | None = None) -> dict:
        total_conversations = await self.repo.get_total_conversations(course_filter=course_filter)
        active_students = await self.repo.get_active_students(course_filter=course_filter)
        total_messages = await self.repo.get_total_messages(course_filter=course_filter)
        avg_questions = await self.repo.get_avg_questions_per_conversation(course_filter=course_filter)

        return {
            "total_conversations": total_conversations,
            "active_students": active_students,
            "total_messages": total_messages,
            "avg_questions_per_conversation": avg_questions,
        }

    async def get_course_overview(self, course_id: str) -> dict:
        return await self.repo.get_course_overview(course_id)

    async def get_course_activity(self, course_id: str, range_param: Literal["7d", "30d", "90d"]) -> list[dict]:
        days = _DAYS_MAP[range_param]
        raw = await self.repo.get_course_activity(course_id, days)
        return _fill_activity_dates(raw, days)

    async def get_course_topics(self, course_id: str) -> list[dict]:
        concepts = await self.repo.get_course_concepts(course_id)

        if not concepts:
            return []

        counter = Counter(c.strip().lower() for c in concepts if c)
        return [{"topic": topic, "count": count} for topic, count in counter.most_common(15)]

    async def get_course_sources(self, course_id: str) -> list[dict]:
        return await self.repo.get_course_sources(course_id)
