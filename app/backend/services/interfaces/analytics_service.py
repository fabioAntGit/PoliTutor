from abc import ABC, abstractmethod
from typing import Literal

from app.backend.schemas.analytics.response import (
    ActivityRead,
    CourseOverviewRead,
    CourseSourcesRead,
    CourseTopicsRead,
    CoursesRead,
    OverviewRead,
)

class IAnalyticsService(ABC):
    @abstractmethod
    async def get_overview(self) -> OverviewRead:
        ...

    @abstractmethod
    async def get_activity(self, range_param: Literal["7d", "30d", "90d"]) -> ActivityRead:
        ...

    @abstractmethod
    async def get_courses(self) -> CoursesRead:  # returns list of course names
        ...

    @abstractmethod
    async def get_course_overview(self, course: str) -> CourseOverviewRead:
        ...

    @abstractmethod
    async def get_course_activity(self, course: str, range_param: Literal["7d", "30d", "90d"]) -> ActivityRead:
        ...

    @abstractmethod
    async def get_course_topics(self, course: str) -> CourseTopicsRead:
        ...

    @abstractmethod
    async def get_course_sources(self, course: str) -> CourseSourcesRead:
        ...
