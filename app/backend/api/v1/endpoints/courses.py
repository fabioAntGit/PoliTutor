from fastapi import APIRouter, Depends, status

from app.backend.schemas.course.response import CourseResponse
from app.backend.schemas.course.request import CourseCreateRequest, CourseUpdateRequest
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
    dependencies=[Depends(require_authenticated)],
)
async def list_courses(
    service: ICourseService = Depends(get_course_service),
):
    courses = await service.list_active_courses()
    return [CourseResponse.model_validate(c.model_dump()) for c in courses]


@router.get(
    "/courses/all",
    response_model=list[CourseResponse],
    dependencies=[Depends(require_admin)],
)
async def list_all_courses(
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
async def create_course(
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
async def update_course(
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
async def delete_course(
    code: str,
    service: ICourseService = Depends(get_course_service),
):
    await service.delete_course(code)
