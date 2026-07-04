from fastapi import APIRouter, Depends, Request, status

from app.backend.core.rate_limit import limiter, user_key
from app.backend.schemas.course.response import CourseResponse
from app.backend.schemas.course.request import CourseCreateRequest, CourseUpdateRequest
from app.backend.schemas.shared.mongo import PyObjectId
from app.backend.schemas.user.enums import UserRole
from app.backend.services.interfaces.course_service import ICourseService
from app.backend.schemas.shared.responses import (
    bad_request,
    conflict,
    forbidden,
    not_found,
    unauthorized,
)
from app.backend.api.deps import (
    get_course_service,
    require_admin,
    require_authenticated,
)

router = APIRouter()


@router.get(
    "/courses",
    response_model=list[CourseResponse],
    summary="List the caller's courses",
    response_description="Active courses the caller can access.",
    responses={**unauthorized()},
)
@limiter.limit("30/minute", key_func=user_key)
async def list_courses(
    request: Request,
    payload: dict = Depends(require_authenticated),
    service: ICourseService = Depends(get_course_service),
):
    if payload.get("role") == UserRole.ADMIN.value:
        courses = await service.list_active_courses()
    else:
        user_id = payload.get("id", "")
        courses = await service.list_user_active_courses(user_id)
    return [CourseResponse.model_validate(c.model_dump(mode="json")) for c in courses]


@router.get(
    "/courses/active",
    response_model=list[CourseResponse],
    summary="List all active courses",
    response_description="Every active course.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not an admin."),
    },
)
@limiter.limit("30/minute", key_func=user_key)
async def list_active_courses(
    request: Request,
    _: dict = Depends(require_admin),
    service: ICourseService = Depends(get_course_service),
):
    courses = await service.list_active_courses()
    return [CourseResponse.model_validate(c.model_dump(mode="json")) for c in courses]


@router.get(
    "/courses/all",
    response_model=list[CourseResponse],
    dependencies=[Depends(require_admin)],
    summary="List all courses, active or not",
    response_description="Every course in the system.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not an admin."),
    },
)
@limiter.limit("30/minute", key_func=user_key)
async def list_all_courses(
    request: Request,
    service: ICourseService = Depends(get_course_service),
):
    courses = await service.list_all_courses()
    return [CourseResponse.model_validate(c.model_dump(mode="json")) for c in courses]


@router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
    summary="Create a course",
    response_description="The newly created course.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not an admin."),
        **conflict("A course with this code or name already exists."),
    },
)
@limiter.limit("10/minute", key_func=user_key)
async def create_course(
    request: Request,
    body: CourseCreateRequest,
    service: ICourseService = Depends(get_course_service),
):
    course = await service.create_course(body.code, body.name, body.scope)
    return CourseResponse.model_validate(course.model_dump(mode="json"))


@router.put(
    "/courses/{course_id}",
    response_model=CourseResponse,
    dependencies=[Depends(require_admin)],
    summary="Update a course",
    response_description="The updated course.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not an admin."),
        **not_found("Course does not exist."),
        **bad_request("No fields to update."),
        **conflict("Another course already uses this name."),
    },
)
@limiter.limit("10/minute", key_func=user_key)
async def update_course(
    request: Request,
    course_id: PyObjectId,
    body: CourseUpdateRequest,
    service: ICourseService = Depends(get_course_service),
):
    update_data = body.model_dump(exclude_unset=True)
    course = await service.update_course(course_id, update_data)
    return CourseResponse.model_validate(course.model_dump(mode="json"))


@router.delete(
    "/courses/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
    summary="Delete a course",
    response_description="The course was removed.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not an admin."),
        **not_found("Course does not exist."),
        **conflict("The course still has users associated and cannot be deleted."),
    },
)
@limiter.limit("5/minute", key_func=user_key)
async def delete_course(
    request: Request,
    course_id: PyObjectId,
    service: ICourseService = Depends(get_course_service),
):
    await service.delete_course(course_id)
