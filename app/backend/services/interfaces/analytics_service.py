from abc import ABC, abstractmethod
from typing import Literal


class IAnalyticsService(ABC):
    @abstractmethod
    async def get_overview(self, course_filter: list[str] | None = None) -> dict:
        ...

    @abstractmethod
    async def get_activity(
        self,
        range_param: Literal["7d", "30d", "90d"],
        course_filter: list[str] | None = None,
    ) -> list[dict]:
        ...

    @abstractmethod
    async def get_courses(self, course_filter: list[str] | None = None) -> list[str]:
        ...

    @abstractmethod
    async def get_course_overview(self, course: str) -> dict:
        ...

    @abstractmethod
    async def get_course_activity(self, course: str, range_param: Literal["7d", "30d", "90d"]) -> list[dict]:
        ...

    @abstractmethod
    async def get_course_topics(self, course: str) -> list[dict]:
        ...

    @abstractmethod
    async def get_course_sources(self, course: str) -> list[dict]:
        ...
