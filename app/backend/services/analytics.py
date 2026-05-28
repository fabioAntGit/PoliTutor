from collections import Counter
from datetime import date, timedelta
from typing import Literal

from app.backend.repositories.interfaces.analytics_repository import IAnalyticsRepository
from app.backend.schemas.analytics.response import (
    ActivityPoint,
    ActivityRead,
    CourseOverviewRead,
    CourseSourcesRead,
    CourseTopicsRead,
    CoursesRead,
    OverviewRead,
    SourcePoint,
    TopicPoint,
)
from app.backend.services.interfaces.analytics_service import IAnalyticsService

_DAYS_MAP = {"7d": 7, "30d": 30, "90d": 90}


# ---------------------------
# Activity helper
# ---------------------------

def _fill_activity_dates(raw: list[dict], days: int) -> ActivityRead:
    counts = {item["date"]: item["questions"] for item in raw}
    today = date.today()
    start = today - timedelta(days=days - 1)

    data = []
    current = start

    while current <= today:
        date_str = current.strftime("%Y-%m-%d")
        data.append(ActivityPoint(date=date_str, questions=counts.get(date_str, 0)))
        current += timedelta(days=1)

    return ActivityRead(data=data)


# ---------------------------
# Service
# ---------------------------

class AnalyticsService(IAnalyticsService):
    def __init__(self, analytics_repository: IAnalyticsRepository) -> None:
        self.repo = analytics_repository

    async def get_activity(
        self,
        range_param: Literal["7d", "30d", "90d"],
        course_filter: list[str] | None = None,
    ) -> ActivityRead:
        days = _DAYS_MAP[range_param]
        raw = await self.repo.get_activity(days, course_filter=course_filter)
        return _fill_activity_dates(raw, days)

    async def get_overview(self, course_filter: list[str] | None = None) -> OverviewRead:
        total_conversations = await self.repo.get_total_conversations(course_filter=course_filter)
        active_students = await self.repo.get_active_students(course_filter=course_filter)
        total_messages = await self.repo.get_total_messages(course_filter=course_filter)
        avg_questions = await self.repo.get_avg_questions_per_conversation(course_filter=course_filter)

        return OverviewRead(
            total_conversations=total_conversations,
            active_students=active_students,
            total_messages=total_messages,
            avg_questions_per_conversation=avg_questions,
        )

    async def get_courses(self, course_filter: list[str] | None = None) -> CoursesRead:
        return CoursesRead(data=await self.repo.get_courses(course_filter=course_filter))

    async def get_course_overview(self, course: str) -> CourseOverviewRead:
        data = await self.repo.get_course_overview(course)
        return CourseOverviewRead(course=course, **data)

    async def get_course_activity(self, course: str, range_param: Literal["7d", "30d", "90d"]) -> ActivityRead:
        days = _DAYS_MAP[range_param]
        raw = await self.repo.get_course_activity(course, days)
        return _fill_activity_dates(raw, days)

    async def get_course_topics(self, course: str) -> CourseTopicsRead:
        concepts = await self.repo.get_course_concepts(course)

        if not concepts:
            return CourseTopicsRead(course=course, topics=[])

        # contar
        counter = Counter(c.strip().lower() for c in concepts if c)

        # ordenar
        top = counter.most_common(15)

        topics = [
            TopicPoint(topic=topic, count=count)
            for topic, count in top
        ]

        return CourseTopicsRead(course=course, topics=topics)

    async def get_course_sources(self, course: str) -> CourseSourcesRead:
        raw = await self.repo.get_course_sources(course)
        return CourseSourcesRead(
            course=course,
            sources=[SourcePoint(**item) for item in raw],
        )
