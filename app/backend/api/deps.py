from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pymongo.asynchronous.database import AsyncDatabase
import redis.asyncio as redis
from pwdlib import PasswordHash

from app.backend.core.database import get_db, get_deprecated_db, get_redis
from app.backend.core.exceptions import AuthError, AccessDeniedError, CourseNotFoundError
from app.backend.schemas.user.enums import UserRole

from app.backend.repositories.analytics import AnalyticsRepository
from app.backend.repositories.deletion import DeletionRepository
from app.backend.repositories.redis import RedisRepository
from app.backend.repositories.reports import ReportRepository
from app.backend.repositories.chats import ChatRepository
from app.backend.repositories.messages import MessageRepository
from app.backend.repositories.user_memory import UserMemoryRepository
from app.backend.repositories.users import UserRepository
from app.backend.repositories.courses import CourseRepository

from app.backend.repositories.interfaces.analytics_repository import IAnalyticsRepository
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.deletion_repository import IDeletionRepository
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.repositories.interfaces.cache_repository import ICacheRepository
from app.backend.repositories.interfaces.report_repository import IReportRepository
from app.backend.repositories.interfaces.user_memory_repository import IUserMemoryRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository

from app.backend.services.chats import ChatService
from app.backend.services.analytics import AnalyticsService
from app.backend.services.context import ContextService
from app.backend.services.messages import MessageService
from app.backend.services.reports import ReportService
from app.backend.services.user_memory import UserMemoryService
from app.backend.services.security import SecurityService
from app.backend.services.authentication import AuthenticationService
from app.backend.services.user import UserService
from app.backend.services.courses import CourseService

from app.backend.services.interfaces.analytics_service import IAnalyticsService
from app.backend.services.interfaces.chat_service import IChatService
from app.backend.services.interfaces.context_service import IContextService
from app.backend.services.interfaces.message_service import IMessageService
from app.backend.services.interfaces.report_service import IReportService
from app.backend.services.interfaces.user_memory_service import IUserMemoryService
from app.backend.services.interfaces.security_service import ISecurityService
from app.backend.services.interfaces.authentication_service import IAuthenticationService
from app.backend.services.interfaces.user_service import IUserService
from app.backend.services.interfaces.course_service import ICourseService

# Repositories

def get_chat_repository(db: AsyncDatabase = Depends(get_db)) -> IChatRepository:
    return ChatRepository(db)

def get_message_repository(db: AsyncDatabase = Depends(get_db)) -> IMessageRepository:
    return MessageRepository(db)

def get_cache_repository(client: redis.Redis = Depends(get_redis)) -> ICacheRepository:
    return RedisRepository(client)

def get_report_repository(db: AsyncDatabase = Depends(get_db)) -> IReportRepository:
    return ReportRepository(db)

def get_analytics_repository(db: AsyncDatabase = Depends(get_db)) -> IAnalyticsRepository:
    return AnalyticsRepository(db)

def get_user_memory_repository(db: AsyncDatabase = Depends(get_db)) -> IUserMemoryRepository:
    return UserMemoryRepository(db)

def get_user_repository(db: AsyncDatabase = Depends(get_db)) -> IUserRepository:
    return UserRepository(db)

def get_course_repository(db: AsyncDatabase = Depends(get_db)) -> ICourseRepository:
    return CourseRepository(db)

def get_deletion_repository(
    db_main: AsyncDatabase = Depends(get_db),
    db_deprecated: AsyncDatabase = Depends(get_deprecated_db),
) -> IDeletionRepository:
    return DeletionRepository(db_main=db_main, db_deprecated=db_deprecated)

# Services

def get_security_service() -> ISecurityService:
    return SecurityService(password_hash=PasswordHash.recommended())

def get_user_memory_service(
    repo: IUserMemoryRepository = Depends(get_user_memory_repository),
) -> IUserMemoryService:
    return UserMemoryService(repo=repo)

def get_analytics_service(
    analytics_repository: IAnalyticsRepository = Depends(get_analytics_repository),
) -> IAnalyticsService:
    return AnalyticsService(analytics_repository=analytics_repository)

def get_context_service(
    message_repository: IMessageRepository = Depends(get_message_repository),
    chat_repository: IChatRepository = Depends(get_chat_repository),
    cache_repository: ICacheRepository = Depends(get_cache_repository),
    user_memory_service: IUserMemoryService = Depends(get_user_memory_service),
) -> IContextService:
    return ContextService(
        message_repository=message_repository,
        chat_repository=chat_repository,
        cache_repository=cache_repository,
        user_memory_service=user_memory_service,
    )

def get_message_service(
    message_repository: IMessageRepository = Depends(get_message_repository),
    chat_repository: IChatRepository = Depends(get_chat_repository),
    cache_repository: ICacheRepository = Depends(get_cache_repository),
    context_service: IContextService = Depends(get_context_service),
    user_memory_service: IUserMemoryService = Depends(get_user_memory_service),
) -> IMessageService:
    return MessageService(
        message_repository=message_repository,
        chat_repository=chat_repository,
        cache_repository=cache_repository,
        context_service=context_service,
        user_memory_service=user_memory_service,
    )

def get_chat_service(
    chat_repository: IChatRepository = Depends(get_chat_repository),
    course_repository: ICourseRepository = Depends(get_course_repository),
    user_repository: IUserRepository = Depends(get_user_repository),
    message_repository: IMessageRepository = Depends(get_message_repository),
) -> IChatService:
    return ChatService(
        chat_repository=chat_repository,
        course_repository=course_repository,
        user_repository=user_repository,
        message_repository=message_repository,
    )

def get_course_service(
    course_repository: ICourseRepository = Depends(get_course_repository),
    user_repository: IUserRepository = Depends(get_user_repository),
) -> ICourseService:
    return CourseService(
        course_repository=course_repository,
        user_repository=user_repository,
    )

def get_report_service(
    report_repository: IReportRepository = Depends(get_report_repository),
    message_repository: IMessageRepository = Depends(get_message_repository),
    chat_repository: IChatRepository = Depends(get_chat_repository),
) -> IReportService:
    return ReportService(
        report_repository=report_repository,
        message_repository=message_repository,
        chat_repository=chat_repository,
    )

def get_authentication_service(
    user_repository: IUserRepository = Depends(get_user_repository),
    security_service: ISecurityService = Depends(get_security_service),
    course_repository: ICourseRepository = Depends(get_course_repository),
    cache_repository: ICacheRepository = Depends(get_cache_repository),
) -> IAuthenticationService:
    return AuthenticationService(
        user_repository=user_repository,
        security_service=security_service,
        course_repository=course_repository,
        cache_repository=cache_repository,
    )

def get_user_service(
    user_repository: IUserRepository = Depends(get_user_repository),
    course_repository: ICourseRepository = Depends(get_course_repository),
    chat_repository: IChatRepository = Depends(get_chat_repository),
    deletion_repository: IDeletionRepository = Depends(get_deletion_repository),
) -> IUserService:
    return UserService(
        user_repository=user_repository,
        course_repository=course_repository,
        chat_repository=chat_repository,
        deletion_repository=deletion_repository,
    )

# Auth guards

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

PASSWORD_CHANGE_ALLOWED_PATHS = {
    "/api/v1/auth/change-password",
}


async def _verify_token(
    token: str,
    security_service: ISecurityService,
    cache_repository: ICacheRepository,
) -> dict:
    if await cache_repository.is_token_blacklisted(token):
        raise AuthError(message="Token invalidado")
    return await security_service.decode_token(token)


def _enforce_password_change(payload: dict, request: Request) -> None:
    if payload.get("must_change_password") and request.url.path not in PASSWORD_CHANGE_ALLOWED_PATHS:
        raise AccessDeniedError(message="Tem de alterar a sua password antes de continuar")


async def require_authenticated(
    request: Request,
    token: str = Depends(oauth2_scheme),
    security_service: ISecurityService = Depends(get_security_service),
    cache_repository: ICacheRepository = Depends(get_cache_repository),
) -> dict:
    payload = await _verify_token(token, security_service, cache_repository)
    _enforce_password_change(payload, request)
    return payload


def require_role(*roles: UserRole):
    async def guard(
        request: Request,
        token: str = Depends(oauth2_scheme),
        security_service: ISecurityService = Depends(get_security_service),
        cache_repository: ICacheRepository = Depends(get_cache_repository),
    ) -> dict:
        payload = await _verify_token(token, security_service, cache_repository)
        allowed = {r.value for r in roles}
        if payload.get("role") not in allowed:
            raise AccessDeniedError(message="Sem permissoes para aceder a este recurso")
        _enforce_password_change(payload, request)
        return payload
    return guard

require_admin = require_role(UserRole.ADMIN)
require_teacher_or_admin = require_role(UserRole.TEACHER, UserRole.ADMIN)


async def _analytics_course_scope(
    course: str,
    payload: dict = Depends(require_teacher_or_admin),
    repo: ICourseRepository = Depends(get_course_repository),
) -> str:
    found = await repo.find_by_code(course)
    if found is None or not found.is_active:
        raise CourseNotFoundError(course)
    if payload.get("role") != UserRole.ADMIN.value:
        if course not in (payload.get("courses") or []):
            raise AccessDeniedError(message="Não tens acesso a esta cadeira.")
    return course


async def _analytics_filter_scope(
    payload: dict = Depends(require_teacher_or_admin),
    repo: ICourseRepository = Depends(get_course_repository),
) -> list[str]:
    active_codes = {c.code for c in await repo.get_active_courses()}
    if payload.get("role") == UserRole.ADMIN.value:
        return sorted(active_codes)
    user_courses = set(payload.get("courses") or [])
    return sorted(user_courses & active_codes)


def analytics_scope(per_course: bool = False):
    return _analytics_course_scope if per_course else _analytics_filter_scope
