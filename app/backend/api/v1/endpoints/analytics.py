from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.backend.api.deps import get_analytics_service
from app.backend.schemas.analytics.response import (
    ActivityRead,
    CourseOverviewRead,
    CourseSourcesRead,
    CourseTopicsRead,
    CoursesRead,
    OverviewRead,
)
from app.backend.services.interfaces.analytics_service import IAnalyticsService

router = APIRouter()


@router.get("/analytics/overview", response_model=OverviewRead)
async def get_overview(service: IAnalyticsService = Depends(get_analytics_service)):
    return await service.get_overview()


@router.get("/analytics/activity", response_model=ActivityRead)
async def get_activity(
    range: Literal["7d", "30d", "90d"] = Query(default="30d"),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    return await service.get_activity(range)


@router.get("/analytics/courses", response_model=CoursesRead)
async def list_courses(service: IAnalyticsService = Depends(get_analytics_service)):
    return await service.get_courses()


@router.get("/analytics/courses/{course}/overview", response_model=CourseOverviewRead)
async def get_course_overview(
    course: str,
    service: IAnalyticsService = Depends(get_analytics_service),
):
    return await service.get_course_overview(course)


@router.get("/analytics/courses/{course}/activity", response_model=ActivityRead)
async def get_course_activity(
    course: str,
    range: Literal["7d", "30d", "90d"] = Query(default="30d"),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    return await service.get_course_activity(course, range)


@router.get("/analytics/courses/{course}/topics", response_model=CourseTopicsRead)
async def get_course_topics(
    course: str,
    service: IAnalyticsService = Depends(get_analytics_service),
):
    return await service.get_course_topics(course)


@router.get("/analytics/courses/{course}/sources", response_model=CourseSourcesRead)
async def get_course_sources(
    course: str,
    service: IAnalyticsService = Depends(get_analytics_service),
):
    return await service.get_course_sources(course)
