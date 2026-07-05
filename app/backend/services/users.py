import logging

from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.deletion_repository import IDeletionRepository
from app.backend.services.interfaces.user_service import IUserService
from app.backend.services.interfaces.security_service import ISecurityService
from app.backend.schemas.user.models import User
from app.backend.core.validators import validate_and_extract_username
from app.backend.core.exceptions import BadRequestError, ConflictError, NotFoundError

logger = logging.getLogger(__name__)


class UserService(IUserService):
    def __init__(
        self,
        user_repository: IUserRepository,
        course_repository: ICourseRepository,
        chat_repository: IChatRepository,
        deletion_repository: IDeletionRepository,
        security_service: ISecurityService,
    ) -> None:
        self.user_repository = user_repository
        self.course_repository = course_repository
        self.chat_repository = chat_repository
        self.deletion_repository = deletion_repository
        self.security_service = security_service

    async def _validate_courses_exist(self, course_ids: list[str]) -> list[str]:
        unique = list(set(course_ids))
        existing = await self.course_repository.get_courses_by_ids(unique)
        if len(existing) != len(unique):
            raise BadRequestError(
                message="Uma ou mais cadeiras fornecidas nao existem no sistema",
                code="validation_error",
            )
        return unique

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str,
        courses: list[str],
    ) -> User:
        username = validate_and_extract_username(email)

        if await self.user_repository.find_by_email(email):
            raise ConflictError(
                message="Ja existe um utilizador com este email",
                code="user_already_exists",
            )
        if await self.user_repository.find_by_username(username):
            raise ConflictError(
                message="Ja existe um utilizador com este username",
                code="user_already_exists",
            )

        course_ids = await self._validate_courses_exist(courses) if courses else []

        hashed_password = await self.security_service.hash_password(password)

        user = User(
            email=email,
            full_name=full_name,
            role=role,
            courses=course_ids,
            hashed_password=hashed_password,
            username=username,
        )
        await self.user_repository.create(user)
        return user

    async def get_user(self, username: str) -> User | None:
        return await self.user_repository.find_by_username(username)

    async def get_users(self) -> list[User]:
        return await self.user_repository.find_all()

    async def update_user(self, username: str, update_data: dict) -> User:
        user = await self.user_repository.find_by_username(username)
        if not user:
            raise NotFoundError(message="Utilizador nao encontrado", code="user_not_found")

        if "email" in update_data and update_data["email"] != user.email:
            new_email = update_data["email"]

            new_username = validate_and_extract_username(new_email)
            update_data["username"] = new_username

            existing_email = await self.user_repository.find_by_email(new_email)
            if existing_email:
                raise ConflictError(
                    message="Este email ja esta em uso por outro utilizador",
                    code="user_already_exists",
                )

            if new_username != username:
                existing_user = await self.user_repository.find_by_username(new_username)
                if existing_user:
                    raise ConflictError(
                        message="Este username (derivado do email) ja esta em uso",
                        code="user_already_exists",
                    )

        if "courses" in update_data:
            courses = update_data["courses"]
            update_data["courses"] = await self._validate_courses_exist(courses) if courses else []

        await self.user_repository.update(username, update_data)

        return user.model_copy(update=update_data)

    async def delete_user(self, username: str) -> bool:
        user = await self.user_repository.find_by_username(username)
        if not user:
            raise NotFoundError(message="Utilizador nao encontrado", code="user_not_found")

        chats = await self.chat_repository.get_chats(user.id)
        conversation_ids = [chat.id for chat in chats if chat.id is not None]
        await self.deletion_repository.move_user_related_docs(
            user_id=user.id,
            username=user.username,
            conversation_ids=conversation_ids,
        )

        logger.info("Account deleted: username=%s id=%s", user.username, user.id)
        return True

    async def change_password(self, username: str, current_password: str, new_password: str) -> User:
        user = await self.user_repository.find_by_username(username)
        if not user:
            raise NotFoundError(message="Utilizador nao encontrado", code="user_not_found")

        if not await self.security_service.verify_password(current_password, user.hashed_password):
            raise BadRequestError(message="Password atual incorreta", code="validation_error")

        new_hash = await self.security_service.hash_password(new_password)
        await self.user_repository.update(
            username,
            {"hashed_password": new_hash, "must_change_password": False},
        )
        return user.model_copy(update={"hashed_password": new_hash, "must_change_password": False})
