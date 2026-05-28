from fastapi import APIRouter, Depends, status

from app.backend.schemas.course.models import Course
from app.backend.schemas.course.response import CourseResponse
from app.backend.schemas.course.request import CourseCreateRequest
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.api.deps import get_course_repository, require_admin
from app.backend.core.exceptions import AppError

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/courses", response_model=list[CourseResponse])
async def list_courses(
    repo: ICourseRepository = Depends(get_course_repository),
):
    courses = await repo.get_active_courses()
    return [CourseResponse.model_validate(c.model_dump()) for c in courses]


@router.post("/courses", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
async def create_course(
    body: CourseCreateRequest,
    repo: ICourseRepository = Depends(get_course_repository),
):
    if await repo.find_by_code(body.code):
        raise AppError(message="Ja existe uma cadeira com esta sigla")
    if await repo.find_by_name(body.name):
        raise AppError(message="Ja existe uma cadeira com este nome")

    course = Course(code=body.code, name=body.name, description=body.description)
    await repo.create(course)
    return CourseResponse.model_validate(course.model_dump())
