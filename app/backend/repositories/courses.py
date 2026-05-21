from pymongo.asynchronous.database import AsyncDatabase
from app.backend.schemas.course.models import Course

from app.backend.repositories.interfaces.course_repository import ICourseRepository

class CourseRepository(ICourseRepository):
    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db["courses"]

    async def create(self, course: Course) -> bool:
        result = await self.collection.insert_one(course.model_dump())
        return result.acknowledged

    async def get_active_courses(self) -> list[Course]:
        courses = []
        async for doc in self.collection.find({"is_active": True}):
            courses.append(Course.model_validate(doc))
        return courses

    async def get_courses_by_codes(self, codes: list[str]) -> list[Course]:
        courses = []
        async for doc in self.collection.find({"code": {"$in": codes}}):
            courses.append(Course.model_validate(doc))
        return courses

    async def find_by_code(self, code: str) -> Course | None:
        doc = await self.collection.find_one({"code": code})
        return Course.model_validate(doc) if doc else None

    async def find_by_name(self, name: str) -> Course | None:
        doc = await self.collection.find_one({"name": name})
        return Course.model_validate(doc) if doc else None
