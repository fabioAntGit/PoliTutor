from typing import Protocol, runtime_checkable

from app.backend.schemas.course.models import Course


@runtime_checkable
class ICourseService(Protocol):
    async def list_active_courses(self) -> list[Course]: ...

    async def list_user_active_courses(self, user_id: str) -> list[Course]: ...

    async def list_all_courses(self) -> list[Course]:
        ...

    async def create_course(self, code: str, name: str, description: str) -> Course:
        ...

    async def update_course(self, code: str, update_data: dict) -> Course:
        ...

    async def delete_course(self, code: str) -> None:
        ...
