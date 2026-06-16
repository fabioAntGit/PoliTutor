from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.cache_repository import ICacheRepository
from app.backend.services.interfaces.security_service import ISecurityService
from app.backend.services.interfaces.authentication_service import IAuthenticationService
from app.backend.schemas.user.models import User
from app.backend.core.exceptions import AuthError
from app.backend.core.validators import validate_and_extract_username
from datetime import datetime, timezone

class AuthenticationService(IAuthenticationService):
    def __init__(
        self,
        user_repository: IUserRepository,
        security_service: ISecurityService,
        course_repository: ICourseRepository,
        cache_repository: ICacheRepository,
    ) -> None:
        self.user_repository = user_repository
        self.security_service = security_service
        self.course_repository = course_repository
        self.cache_repository = cache_repository

    async def login(self, username: str, password: str) -> str:
        user = await self.user_repository.find_by_username(username)
        if not user:
            raise AuthError(message="Username ou senha invalidos")
        if not await self.security_service.verify_password(password, user.hashed_password):
            raise AuthError(message="Username ou senha invalidos")

        payload = {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value,
            "courses": user.courses,
            "must_change_password": user.must_change_password,
        }

        return await self.security_service.create_access_token(payload)

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str,
        courses: list[str],
    ) -> bool:
        username = validate_and_extract_username(email)

        user = await self.user_repository.find_by_username(username)
        if user:
            raise AuthError(message="Username (derivado do email) ja existe")

        user = await self.user_repository.find_by_email(email)
        if user:
            raise AuthError(message="Email ja existe")

        if courses:
            unique_courses = list(set(courses))
            existing_courses = await self.course_repository.get_courses_by_codes(unique_courses)
            if len(existing_courses) != len(unique_courses):
                raise AuthError(message="Uma ou mais cadeiras fornecidas nao existem no sistema")

        hashed_password = await self.security_service.hash_password(password)

        user = User(
            email=email,
            full_name=full_name,
            role=role,
            courses=courses,
            hashed_password=hashed_password,
            username=username,
        )

        return await self.user_repository.create(user)

    async def logout(self, access_token: str) -> bool:
        now_timestamp = datetime.now(timezone.utc).timestamp()
        try:
            payload = await self.security_service.decode_token(access_token)
            exp = payload.get("exp")
            if exp:
                expire_in_seconds = int(exp - now_timestamp)
                if expire_in_seconds > 0:
                    await self.cache_repository.add_token_to_blacklist(access_token, expire_in_seconds)
        except AuthError:
            pass
        return True
