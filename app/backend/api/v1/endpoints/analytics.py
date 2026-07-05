from typing import Literal

from fastapi import APIRouter, Depends, Query, Request

from app.backend.api.deps import (
    analytics_scope,
    get_analytics_service,
    require_teacher_or_admin,
)
from app.backend.core.rate_limit import limiter, user_key
from app.backend.schemas.analytics.response import (
    ActivityPoint,
    ActivityRead,
    CourseOverviewRead,
    CourseSourcesRead,
    CourseTopicsRead,
    OverviewRead,
    SourcePoint,
    TopicPoint,
)
from app.backend.schemas.shared.responses import forbidden, not_found, unauthorized
from app.backend.services.interfaces.analytics_service import IAnalyticsService

router = APIRouter(dependencies=[Depends(require_teacher_or_admin)])

RANGE_QUERY = Query(
    default="30d",
    description="Time window for the activity series: last 7, 30 or 90 days.",
)


@router.get(
    "/analytics/overview",
    response_model=OverviewRead,
    summary="Aggregate overview metrics",
    response_description="Totals across the caller's courses.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not a teacher or admin."),
    },
)
@limiter.limit("20/minute", key_func=user_key)
async def get_overview(
    request: Request,
    course_filter: list[str] = Depends(analytics_scope()),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    data = await service.get_overview(course_filter=course_filter)
    return OverviewRead(**data)


@router.get(
    "/analytics/activity",
    response_model=ActivityRead,
    summary="Question activity over time",
    response_description="Daily count of student questions within the selected range.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not a teacher or admin."),
    },
)
@limiter.limit("20/minute", key_func=user_key)
async def get_activity(
    request: Request,
    range: Literal["7d", "30d", "90d"] = RANGE_QUERY,
    course_filter: list[str] = Depends(analytics_scope()),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    data = await service.get_activity(range, course_filter=course_filter)
    return ActivityRead(data=[ActivityPoint(**point) for point in data])


@router.get(
    "/analytics/courses/{course_id}/overview",
    response_model=CourseOverviewRead,
    summary="Overview metrics for a single course",
    response_description="Usage totals scoped to one course.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not a teacher/admin, or lacks access to this course."),
        **not_found("Course does not exist or is inactive."),
    },
)
@limiter.limit("20/minute", key_func=user_key)
async def get_course_overview(
    request: Request,
    course_id: str = Depends(analytics_scope(per_course=True)),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    data = await service.get_course_overview(course_id)
    return CourseOverviewRead(**data)


@router.get(
    "/analytics/courses/{course_id}/activity",
    response_model=ActivityRead,
    summary="Question activity over time for a single course",
    response_description="Daily count of student questions for one course.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not a teacher/admin, or lacks access to this course."),
        **not_found("Course does not exist or is inactive."),
    },
)
@limiter.limit("20/minute", key_func=user_key)
async def get_course_activity(
    request: Request,
    course_id: str = Depends(analytics_scope(per_course=True)),
    range: Literal["7d", "30d", "90d"] = RANGE_QUERY,
    service: IAnalyticsService = Depends(get_analytics_service),
):
    data = await service.get_course_activity(course_id, range)
    return ActivityRead(data=[ActivityPoint(**point) for point in data])


@router.get(
    "/analytics/courses/{course_id}/topics",
    response_model=CourseTopicsRead,
    summary="Most frequent topics for a course",
    response_description="Top topics ranked by how often students asked about them.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not a teacher/admin, or lacks access to this course."),
        **not_found("Course does not exist or is inactive."),
    },
)
@limiter.limit("20/minute", key_func=user_key)
async def get_course_topics(
    request: Request,
    course_id: str = Depends(analytics_scope(per_course=True)),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    topics = await service.get_course_topics(course_id)
    return CourseTopicsRead(topics=[TopicPoint(**topic) for topic in topics])


@router.get(
    "/analytics/courses/{course_id}/sources",
    response_model=CourseSourcesRead,
    summary="Most referenced sources for a course",
    response_description="Source documents ranked by how often they were cited.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not a teacher/admin, or lacks access to this course."),
        **not_found("Course does not exist or is inactive."),
    },
)
@limiter.limit("20/minute", key_func=user_key)
async def get_course_sources(
    request: Request,
    course_id: str = Depends(analytics_scope(per_course=True)),
    service: IAnalyticsService = Depends(get_analytics_service),
):
    sources = await service.get_course_sources(course_id)
    return CourseSourcesRead(sources=[SourcePoint(**source) for source in sources])
