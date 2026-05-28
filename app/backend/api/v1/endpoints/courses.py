from fastapi import APIRouter, Depends, status

from app.backend.schemas.course.models import Course
from app.backend.schemas.course.response import CourseResponse
from app.backend.schemas.course.request import CourseCreateRequest, CourseUpdateRequest
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.api.deps import (
    get_course_repository,
    get_user_repository,
    require_admin,
    require_authenticated,
)
from app.backend.core.exceptions import AppError, CourseNotFoundError

router = APIRouter()


@router.get(
    "/courses",
    response_model=list[CourseResponse],
    dependencies=[Depends(require_authenticated)],
)
async def list_courses(
    repo: ICourseRepository = Depends(get_course_repository),
):
    courses = await repo.get_active_courses()
    return [CourseResponse.model_validate(c.model_dump()) for c in courses]


@router.get(
    "/courses/all",
    response_model=list[CourseResponse],
    dependencies=[Depends(require_admin)],
)
async def list_all_courses(
    repo: ICourseRepository = Depends(get_course_repository),
):
    courses = await repo.get_all_courses()
    return [CourseResponse.model_validate(c.model_dump()) for c in courses]


@router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
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


@router.put(
    "/courses/{code}",
    response_model=CourseResponse,
    dependencies=[Depends(require_admin)],
)
async def update_course(
    code: str,
    body: CourseUpdateRequest,
    repo: ICourseRepository = Depends(get_course_repository),
):
    course = await repo.find_by_code(code)
    if course is None:
        raise CourseNotFoundError(code)

    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise AppError(message="Nenhum campo para atualizar")

    if "name" in update_data and update_data["name"] != course.name:
        existing = await repo.find_by_name(update_data["name"])
        if existing is not None and existing.code != code:
            raise AppError(message="Ja existe uma cadeira com este nome")

    await repo.update(code, update_data)
    updated = await repo.find_by_code(code)
    return CourseResponse.model_validate(updated.model_dump())


@router.delete(
    "/courses/{code}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_course(
    code: str,
    course_repo: ICourseRepository = Depends(get_course_repository),
    user_repo: IUserRepository = Depends(get_user_repository),
):
    course = await course_repo.find_by_code(code)
    if course is None:
        raise CourseNotFoundError(code)

    associated = await user_repo.count_with_course(code)
    if associated > 0:
        raise AppError(
            message=(
                f"Esta cadeira tem {associated} utilizador(es) associado(s). "
                "Desassocia-os ou desativa a cadeira antes de eliminar."
            )
        )

    await course_repo.delete(code)
