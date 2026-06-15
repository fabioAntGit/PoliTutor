from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.backend.api.deps import (
    analytics_scope,
    get_analytics_service,
    require_teacher_or_admin,
)
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

router = APIRouter(dependencies=[Depends(require_teacher_or_admin)])


@router.get("/analytics/overview", response_model=OverviewRead)
async def get_overview(
    course_filter: list[str] = Depends(analytics_scope()),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    data = await service.get_overview(course_filter=course_filter)
    return OverviewRead(**data)


@router.get("/analytics/activity", response_model=ActivityRead)
async def get_activity(
    range: Literal["7d", "30d", "90d"] = Query(default="30d"),
    course_filter: list[str] = Depends(analytics_scope()),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    data = await service.get_activity(range, course_filter=course_filter)
    return ActivityRead(data=[ActivityPoint(**point) for point in data])


@router.get("/analytics/courses", response_model=CoursesRead)
async def list_courses(
    course_filter: list[str] = Depends(analytics_scope()),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    data = await service.get_courses(course_filter=course_filter)
    return CoursesRead(data=data)


@router.get("/analytics/courses/{course}/overview", response_model=CourseOverviewRead)
async def get_course_overview(
    course: str = Depends(analytics_scope(per_course=True)),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    data = await service.get_course_overview(course)
    return CourseOverviewRead(course=course, **data)


@router.get("/analytics/courses/{course}/activity", response_model=ActivityRead)
async def get_course_activity(
    course: str = Depends(analytics_scope(per_course=True)),
    range: Literal["7d", "30d", "90d"] = Query(default="30d"),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    data = await service.get_course_activity(course, range)
    return ActivityRead(data=[ActivityPoint(**point) for point in data])


@router.get("/analytics/courses/{course}/topics", response_model=CourseTopicsRead)
async def get_course_topics(
    course: str = Depends(analytics_scope(per_course=True)),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    topics = await service.get_course_topics(course)
    return CourseTopicsRead(course=course, topics=[TopicPoint(**topic) for topic in topics])


@router.get("/analytics/courses/{course}/sources", response_model=CourseSourcesRead)
async def get_course_sources(
    course: str = Depends(analytics_scope(per_course=True)),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    sources = await service.get_course_sources(course)
    return CourseSourcesRead(course=course, sources=[SourcePoint(**source) for source in sources])
