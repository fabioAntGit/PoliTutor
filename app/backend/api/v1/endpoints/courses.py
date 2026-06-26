from fastapi import APIRouter, Depends, Request, status

from app.backend.core.rate_limit import limiter, user_key
from app.backend.schemas.course.response import CourseResponse
from app.backend.schemas.course.request import CourseCreateRequest, CourseUpdateRequest
from app.backend.schemas.user.enums import UserRole
from app.backend.services.interfaces.course_service import ICourseService
from app.backend.api.deps import (
    get_course_service,
    require_admin,
    require_authenticated,
)

router = APIRouter()


@router.get(
    "/courses",
    response_model=list[CourseResponse],
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
    return [CourseResponse.model_validate(c.model_dump()) for c in courses]


@router.get(
    "/courses/active",
    response_model=list[CourseResponse],
)
@limiter.limit("30/minute", key_func=user_key)
async def list_active_courses(
    request: Request,
    _: dict = Depends(require_admin),
    service: ICourseService = Depends(get_course_service),
):
    courses = await service.list_active_courses()
    return [CourseResponse.model_validate(c.model_dump()) for c in courses]


@router.get(
    "/courses/all",
    response_model=list[CourseResponse],
    dependencies=[Depends(require_admin)],
)
@limiter.limit("30/minute", key_func=user_key)
async def list_all_courses(
    request: Request,
    service: ICourseService = Depends(get_course_service),
):
    courses = await service.list_all_courses()
    return [CourseResponse.model_validate(c.model_dump()) for c in courses]


@router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
@limiter.limit("10/minute", key_func=user_key)
async def create_course(
    request: Request,
    body: CourseCreateRequest,
    service: ICourseService = Depends(get_course_service),
):
    course = await service.create_course(body.code, body.name, body.description)
    return CourseResponse.model_validate(course.model_dump())


@router.put(
    "/courses/{code}",
    response_model=CourseResponse,
    dependencies=[Depends(require_admin)],
)
@limiter.limit("10/minute", key_func=user_key)
async def update_course(
    request: Request,
    code: str,
    body: CourseUpdateRequest,
    service: ICourseService = Depends(get_course_service),
):
    update_data = body.model_dump(exclude_unset=True)
    course = await service.update_course(code, update_data)
    return CourseResponse.model_validate(course.model_dump())


@router.delete(
    "/courses/{code}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
@limiter.limit("5/minute", key_func=user_key)
async def delete_course(
    request: Request,
    code: str,
    service: ICourseService = Depends(get_course_service),
):
    await service.delete_course(code)
