import logging

from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.deletion_repository import IDeletionRepository
from app.backend.services.interfaces.user_service import IUserService
from app.backend.schemas.user.models import User
from app.backend.core.validators import validate_and_extract_username
from app.backend.core.exceptions import AppError, UserNotFoundError, UserAlreadyExistsError, ValidationError
from pwdlib import PasswordHash

logger = logging.getLogger(__name__)


class UserService(IUserService):
    def __init__(
        self,
        user_repository: IUserRepository,
        course_repository: ICourseRepository,
        chat_repository: IChatRepository,
        deletion_repository: IDeletionRepository,
    ) -> None:
        self.user_repository = user_repository
        self.course_repository = course_repository
        self.chat_repository = chat_repository
        self.deletion_repository = deletion_repository

    async def create_user(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str,
        courses: list[str]
    ) -> User:
        if len(password) < 8:
            raise ValidationError(message="A password deve ter pelo menos 8 caracteres")

        username = validate_and_extract_username(email)

        if await self.user_repository.find_by_email(email):
            raise UserAlreadyExistsError(message="Ja existe um utilizador com este email")
        if await self.user_repository.find_by_username(username):
            raise UserAlreadyExistsError(message="Ja existe um utilizador com este username")

        if courses:
            unique_courses = list(set(courses))
            existing_courses = await self.course_repository.get_courses_by_codes(unique_courses)
            if len(existing_courses) != len(unique_courses):
                raise ValidationError(message="Uma ou mais cadeiras fornecidas nao existem no sistema")
            courses = unique_courses

        password_hash = PasswordHash.recommended()
        hashed_password = password_hash.hash(password)

        user = User(
            email=email,
            full_name=full_name,
            role=role,
            courses=courses,
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
        user = await self.get_user(username)
        if not user:
            raise UserNotFoundError()

        new_username = username

        if "email" in update_data and update_data["email"] != user.email:
            new_email = update_data["email"]

            new_username = validate_and_extract_username(new_email)
            update_data["username"] = new_username

            existing_email = await self.user_repository.find_by_email(new_email)
            if existing_email:
                raise UserAlreadyExistsError(message="Este email ja esta em uso por outro utilizador")

            if new_username != username:
                existing_user = await self.user_repository.find_by_username(new_username)
                if existing_user:
                    raise UserAlreadyExistsError(message="Este username (derivado do email) ja esta em uso")

        if "courses" in update_data:
            courses = update_data["courses"]
            if courses:
                unique_courses = list(set(courses))
                existing_courses = await self.course_repository.get_courses_by_codes(unique_courses)
                if len(existing_courses) != len(unique_courses):
                    raise ValidationError(message="Uma ou mais cadeiras fornecidas nao existem no sistema")
                update_data["courses"] = unique_courses
            else:
                update_data["courses"] = []

        await self.user_repository.update(username, update_data)

        return user.model_copy(update=update_data)

    async def delete_user(self, username: str) -> bool:
        user = await self.get_user(username)
        if not user:
            raise UserNotFoundError()

        chats = await self.chat_repository.get_chats(user.id)
        conversation_ids = [str(chat.id) for chat in chats if chat.id is not None]

        if conversation_ids:
            await self.deletion_repository.move_docs(
                "messages", {"conversation_id": {"$in": conversation_ids}}
            )
            await self.deletion_repository.move_docs(
                "reports", {"conversation_id": {"$in": conversation_ids}}
            )

        await self.deletion_repository.move_docs("chats", {"user_id": user.id})
        await self.deletion_repository.move_docs("user_memory", {"user_id": user.id})
        await self.deletion_repository.move_docs("users", {"username": user.username})

        logger.info("Account deleted: username=%s id=%s", user.username, user.id)
        return True

    async def change_password(self, username: str, current_password: str, new_password: str) -> User:
        user = await self.get_user(username)
        if not user:
            raise UserNotFoundError()

        password_hash = PasswordHash.recommended()
        if not password_hash.verify(current_password, user.hashed_password):
            raise ValidationError(message="Password atual incorreta")

        if len(new_password) < 8:
            raise ValidationError(message="A nova password deve ter pelo menos 8 caracteres")

        new_hash = password_hash.hash(new_password)
        await self.user_repository.update(
            username,
            {"hashed_password": new_hash, "must_change_password": False},
        )
        return user.model_copy(update={"hashed_password": new_hash, "must_change_password": False})
