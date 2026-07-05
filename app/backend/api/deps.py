from functools import lru_cache

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from pymongo.asynchronous.database import AsyncDatabase
import redis.asyncio as redis
from pwdlib import PasswordHash

from rag.src.runtime.engine import get_engine
from contracts.rag.interfaces import IRagEngine
from app.backend.gateways.interfaces.model_client import IModelClient

from app.backend.core.database import get_db, get_deprecated_db, get_redis
from app.backend.core.exceptions import AccessDeniedError
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
from app.backend.gateways.model_client import OpenRouterModelClient

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
from app.backend.services.users import UserService
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


@lru_cache
def get_model_client() -> IModelClient:
    return OpenRouterModelClient()


def get_security_service() -> ISecurityService:
    return SecurityService(password_hash=PasswordHash.recommended())


def get_user_memory_service(
    repo: IUserMemoryRepository = Depends(get_user_memory_repository),
    model_client: IModelClient = Depends(get_model_client),
    course_repository: ICourseRepository = Depends(get_course_repository),
) -> IUserMemoryService:
    return UserMemoryService(repo=repo, model_client=model_client, course_repository=course_repository)


def get_analytics_service(
    analytics_repository: IAnalyticsRepository = Depends(get_analytics_repository),
    course_repository: ICourseRepository = Depends(get_course_repository),
    user_repository: IUserRepository = Depends(get_user_repository),
) -> IAnalyticsService:
    return AnalyticsService(
        analytics_repository=analytics_repository,
        course_repository=course_repository,
        user_repository=user_repository,
    )


def get_context_service(
    message_repository: IMessageRepository = Depends(get_message_repository),
    chat_repository: IChatRepository = Depends(get_chat_repository),
    cache_repository: ICacheRepository = Depends(get_cache_repository),
    user_memory_service: IUserMemoryService = Depends(get_user_memory_service),
    model_client: IModelClient = Depends(get_model_client),
) -> IContextService:
    return ContextService(
        message_repository=message_repository,
        chat_repository=chat_repository,
        cache_repository=cache_repository,
        user_memory_service=user_memory_service,
        model_client=model_client,
    )


@lru_cache
def get_rag_engine() -> IRagEngine:
    return get_engine()


def get_message_service(
    message_repository: IMessageRepository = Depends(get_message_repository),
    chat_repository: IChatRepository = Depends(get_chat_repository),
    course_repository: ICourseRepository = Depends(get_course_repository),
    cache_repository: ICacheRepository = Depends(get_cache_repository),
    context_service: IContextService = Depends(get_context_service),
    user_memory_service: IUserMemoryService = Depends(get_user_memory_service),
    rag_engine: IRagEngine = Depends(get_rag_engine),
) -> IMessageService:
    return MessageService(
        message_repository=message_repository,
        chat_repository=chat_repository,
        course_repository=course_repository,
        cache_repository=cache_repository,
        context_service=context_service,
        user_memory_service=user_memory_service,
        rag_engine=rag_engine,
    )


def get_chat_service(
    chat_repository: IChatRepository = Depends(get_chat_repository),
    course_repository: ICourseRepository = Depends(get_course_repository),
    user_repository: IUserRepository = Depends(get_user_repository),
    message_repository: IMessageRepository = Depends(get_message_repository),
    report_repository: IReportRepository = Depends(get_report_repository),
) -> IChatService:
    return ChatService(
        chat_repository=chat_repository,
        course_repository=course_repository,
        user_repository=user_repository,
        message_repository=message_repository,
        report_repository=report_repository,
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
    cache_repository: ICacheRepository = Depends(get_cache_repository),
) -> IAuthenticationService:
    return AuthenticationService(
        user_repository=user_repository,
        security_service=security_service,
        cache_repository=cache_repository,
    )


def get_user_service(
    user_repository: IUserRepository = Depends(get_user_repository),
    course_repository: ICourseRepository = Depends(get_course_repository),
    chat_repository: IChatRepository = Depends(get_chat_repository),
    deletion_repository: IDeletionRepository = Depends(get_deletion_repository),
    security_service: ISecurityService = Depends(get_security_service),
) -> IUserService:
    return UserService(
        user_repository=user_repository,
        course_repository=course_repository,
        chat_repository=chat_repository,
        deletion_repository=deletion_repository,
        security_service=security_service,
    )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

PASSWORD_CHANGE_ALLOWED_PATHS = {
    "/api/v1/auth/change-password",
}

def _enforce_password_change(payload: dict, request: Request) -> None:
    if payload.get("must_change_password") and request.url.path not in PASSWORD_CHANGE_ALLOWED_PATHS:
        raise AccessDeniedError(message="Tem de alterar a sua password antes de continuar")


async def require_authenticated(
    request: Request,
    token: str = Depends(oauth2_scheme),
    authentication_service: IAuthenticationService = Depends(get_authentication_service),
) -> dict:
    payload = await authentication_service.verify_token(token)
    _enforce_password_change(payload, request)
    return payload


def require_role(*roles: UserRole):
    async def guard(
        request: Request,
        token: str = Depends(oauth2_scheme),
        authentication_service: IAuthenticationService = Depends(get_authentication_service),
    ) -> dict:
        payload = await authentication_service.verify_token(token)
        allowed = {r.value for r in roles}
        if payload.get("role") not in allowed:
            raise AccessDeniedError(message="Sem permissoes para aceder a este recurso")
        _enforce_password_change(payload, request)
        return payload
    return guard

require_admin = require_role(UserRole.ADMIN)
require_teacher_or_admin = require_role(UserRole.TEACHER, UserRole.ADMIN)


async def _analytics_course_scope(
    course_id: str,
    payload: dict = Depends(require_teacher_or_admin),
    service: IAnalyticsService = Depends(get_analytics_service),
) -> str:
    return await service.resolve_course_scope(course_id, payload)


async def _analytics_filter_scope(
    payload: dict = Depends(require_teacher_or_admin),
    service: IAnalyticsService = Depends(get_analytics_service),
) -> list[str]:
    return await service.resolve_filter_scope(payload)


def analytics_scope(per_course: bool = False):
    return _analytics_course_scope if per_course else _analytics_filter_scope
