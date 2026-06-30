from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase
from app.backend.schemas.course.models import Course

from app.backend.repositories.interfaces.course_repository import ICourseRepository

class CourseRepository(ICourseRepository):
    def __init__(self, db: AsyncDatabase) -> None:
        self.collection = db["courses"]

    async def create(self, course: Course) -> str:
        result = await self.collection.insert_one(course.model_dump(exclude={"id"}, by_alias=True))
        return str(result.inserted_id)

    async def get_active_courses(self) -> list[Course]:
        courses = []
        async for doc in self.collection.find({"is_active": True}):
            courses.append(Course.model_validate(doc))
        return courses

    async def get_courses_by_ids(self, ids: list[str]) -> list[Course]:
        object_ids = [ObjectId(i) for i in ids]
        courses = []
        async for doc in self.collection.find({"_id": {"$in": object_ids}}):
            courses.append(Course.model_validate(doc))
        return courses

    async def find_by_code(self, code: str) -> Course | None:
        doc = await self.collection.find_one({"code": code})
        return Course.model_validate(doc) if doc else None

    async def find_by_id(self, course_id: str) -> Course | None:
        try:
            oid = ObjectId(course_id)
        except Exception:
            return None
        doc = await self.collection.find_one({"_id": oid})
        return Course.model_validate(doc) if doc else None

    async def find_by_name(self, name: str) -> Course | None:
        doc = await self.collection.find_one({"name": name})
        return Course.model_validate(doc) if doc else None

    async def get_all_courses(self) -> list[Course]:
        courses = []
        async for doc in self.collection.find({}):
            courses.append(Course.model_validate(doc))
        return courses

    async def update(self, course_id: str, fields: dict) -> bool:
        result = await self.collection.update_one(
            {"_id": ObjectId(course_id)},
            {"$set": fields},
        )
        return result.matched_count > 0

    async def delete(self, course_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(course_id)})
        return result.deleted_count > 0
