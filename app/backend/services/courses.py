from app.backend.core.exceptions import AppError, CourseNotFoundError, CourseAlreadyExistsError, CourseInUseError, ValidationError
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.schemas.course.models import Course
from app.backend.services.interfaces.course_service import ICourseService


class CourseService(ICourseService):
    def __init__(
        self,
        course_repository: ICourseRepository,
        user_repository: IUserRepository,
    ) -> None:
        self.course_repository = course_repository
        self.user_repository = user_repository

    async def list_active_courses(self) -> list[Course]:
        return await self.course_repository.get_active_courses()

    async def list_user_active_courses(self, user_id: str) -> list[Course]:
        user = await self.user_repository.find_by_id(user_id)
        if not user or not user.courses:
            return []
        courses = await self.course_repository.get_courses_by_codes(user.courses)
        return [c for c in courses if c.is_active]

    async def list_all_courses(self) -> list[Course]:
        return await self.course_repository.get_all_courses()

    async def create_course(self, code: str, name: str, description: str) -> Course:
        if await self.course_repository.find_by_code(code):
            raise CourseAlreadyExistsError(message="Ja existe uma cadeira com esta sigla")
        if await self.course_repository.find_by_name(name):
            raise CourseAlreadyExistsError(message="Ja existe uma cadeira com este nome")

        course = Course(code=code, name=name, description=description)
        await self.course_repository.create(course)
        return course

    async def update_course(self, code: str, update_data: dict) -> Course:
        course = await self.course_repository.find_by_code(code)
        if course is None:
            raise CourseNotFoundError(code)

        if not update_data:
            raise ValidationError(message="Nenhum campo para atualizar")

        if "name" in update_data and update_data["name"] != course.name:
            existing = await self.course_repository.find_by_name(update_data["name"])
            if existing is not None and existing.code != code:
                raise CourseAlreadyExistsError(message="Ja existe uma cadeira com este nome")

        await self.course_repository.update(code, update_data)
        updated = await self.course_repository.find_by_code(code)
        return updated

    async def delete_course(self, code: str) -> None:
        course = await self.course_repository.find_by_code(code)
        if course is None:
            raise CourseNotFoundError(code)

        associated = await self.user_repository.count_with_course(code)
        if associated > 0:
            raise CourseInUseError(
                message=(
                    f"Esta cadeira tem {associated} utilizador(es) associado(s). "
                    "Desassocia-os ou desativa a cadeira antes de eliminar."
                )
            )

        await self.course_repository.delete(code)
