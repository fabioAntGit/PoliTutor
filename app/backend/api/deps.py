from fastapi import Depends
from pymongo.asynchronous.database import AsyncDatabase
import redis.asyncio as redis

from app.backend.core.database import get_db, get_redis

from app.backend.repositories.analytics import AnalyticsRepository
from app.backend.repositories.redis import RedisRepository
from app.backend.repositories.reports import ReportRepository
from app.backend.repositories.chats import ChatRepository
from app.backend.repositories.messages import MessageRepository

from app.backend.services.chats import ChatService
from app.backend.services.analytics import AnalyticsService
from app.backend.services.context import ContextService
from app.backend.services.messages import MessageService
from app.backend.services.projects import ProjectService
from app.backend.services.reports import ReportService

from app.backend.services.interfaces.analytics_service import IAnalyticsService
from app.backend.services.interfaces.chat_service import IChatService
from app.backend.services.interfaces.context_service import IContextService
from app.backend.services.interfaces.message_service import IMessageService
from app.backend.services.interfaces.project_service import IProjectService
from app.backend.services.interfaces.report_service import IReportService

from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.repositories.interfaces.redis_repository import IRedisRepository
from app.backend.repositories.interfaces.report_repository import IReportRepository

def get_chat_repository(db: AsyncDatabase = Depends(get_db)) -> IChatRepository:
    return ChatRepository(db)

def get_message_repository(db: AsyncDatabase = Depends(get_db)) -> IMessageRepository:
    return MessageRepository(db)

def get_redis_repository(client: redis.Redis = Depends(get_redis)) -> IRedisRepository:
    return RedisRepository(client)

def get_report_repository(db: AsyncDatabase = Depends(get_db)) -> IReportRepository:
    return ReportRepository(db)

def get_analytics_repository(db: AsyncDatabase = Depends(get_db)) -> AnalyticsRepository:
    return AnalyticsRepository(db)

def get_analytics_service(
    analytics_repository: AnalyticsRepository = Depends(get_analytics_repository),
) -> IAnalyticsService:
    return AnalyticsService(analytics_repository=analytics_repository)

def get_context_service(
    message_repository: IMessageRepository = Depends(get_message_repository),
    chat_repository: IChatRepository = Depends(get_chat_repository),
    redis_repository: IRedisRepository = Depends(get_redis_repository),
) -> IContextService:
    return ContextService(
        message_repository=message_repository,
        chat_repository=chat_repository,
        redis_repository=redis_repository,
    )

def get_message_service(
    message_repository: IMessageRepository = Depends(get_message_repository),
    chat_repository: IChatRepository = Depends(get_chat_repository),
    redis_repository: IRedisRepository = Depends(get_redis_repository),
    context_service: IContextService = Depends(get_context_service),
) -> IMessageService:
    return MessageService(
        message_repository=message_repository,
        chat_repository=chat_repository,
        redis_repository=redis_repository,
        context_service=context_service,
    )


def get_chat_service(
    chat_repository: IChatRepository = Depends(get_chat_repository),
    message_service: IMessageService = Depends(get_message_service),
) -> IChatService:
    return ChatService(
        chat_repository=chat_repository,
        message_service=message_service,
    )


def get_project_service() -> IProjectService:
    return ProjectService()

def get_report_service(
    repository: IReportRepository = Depends(get_report_repository),
    message_repository: IMessageRepository = Depends(get_message_repository),
    chat_repository: IChatRepository = Depends(get_chat_repository),
) -> IReportService:
    return ReportService(
        repository=repository,
        message_repository=message_repository,
        chat_repository=chat_repository,
    )
