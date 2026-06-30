from typing import Protocol, runtime_checkable, Literal


@runtime_checkable
class IAnalyticsService(Protocol):
    async def get_overview(self, course_filter: list[str] | None = None) -> dict: ...

    async def get_activity(
        self,
        range_param: Literal["7d", "30d", "90d"],
        course_filter: list[str] | None = None,
    ) -> list[dict]: ...

    async def get_course_overview(self, course_id: str) -> dict: ...

    async def get_course_activity(self, course_id: str, range_param: Literal["7d", "30d", "90d"]) -> list[dict]: ...

    async def get_course_topics(self, course_id: str) -> list[dict]: ...

    async def get_course_sources(self, course_id: str) -> list[dict]: ...
