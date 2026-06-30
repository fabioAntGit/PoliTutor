from unittest.mock import AsyncMock, Mock

import pytest
from bson import ObjectId

from app.backend.core.exceptions import AccessDeniedError, NotFoundError
from app.backend.repositories.interfaces.cache_repository import ICacheRepository
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.schemas.chat.models import Chat
from app.backend.schemas.course.models import Course
from app.backend.schemas.message.enums import Role
from app.backend.services.interfaces.context_service import IContextService
from app.backend.services.interfaces.user_memory_service import IUserMemoryService
from app.backend.services.messages import MessageService
from contracts.rag.interfaces import IRagEngine
from contracts.rag.models import TutorResponse, TutorSource


CONVERSATION_ID = "60d5ecb8b4259b3a0c4f1a01"
USER_ID = str(ObjectId())
OTHER_USER_ID = str(ObjectId())
ED_ID = str(ObjectId())
USER_MESSAGE_ID = "60d5ecb8b4259b3a0c4f1a02"
ASSISTANT_MESSAGE_ID = "60d5ecb8b4259b3a0c4f1a03"


def _make_chat(**kwargs) -> Chat:
    defaults = dict(
        _id=CONVERSATION_ID,
        course_id=ED_ID,
        user_id=USER_ID,
        summary=None,
    )
    defaults.update(kwargs)
    return Chat(**defaults)


def _make_course(**kwargs) -> Course:
    defaults = dict(_id=ED_ID, code="ed", name="Estruturas de Dados", is_active=True)
    defaults.update(kwargs)
    return Course(**defaults)


@pytest.fixture
def message_repo():
    return AsyncMock(spec=IMessageRepository)


@pytest.fixture
def chat_repo():
    return AsyncMock(spec=IChatRepository)


@pytest.fixture
def course_repo():
    repo = AsyncMock(spec=ICourseRepository)
    repo.find_by_id.return_value = _make_course()
    return repo


@pytest.fixture
def cache_repo():
    return AsyncMock(spec=ICacheRepository)


@pytest.fixture
def context_service():
    return AsyncMock(spec=IContextService)


@pytest.fixture
def user_memory_service():
    return AsyncMock(spec=IUserMemoryService)


@pytest.fixture
def rag_engine():
    return Mock(spec=IRagEngine)


@pytest.fixture
def service(message_repo, chat_repo, course_repo, cache_repo, context_service, user_memory_service, rag_engine):
    return MessageService(
        message_repository=message_repo,
        chat_repository=chat_repo,
        course_repository=course_repo,
        cache_repository=cache_repo,
        context_service=context_service,
        user_memory_service=user_memory_service,
        rag_engine=rag_engine,
    )


async def test_send_message_persists_user_and_assistant_messages_and_returns_rag_response(
    service,
    message_repo,
    chat_repo,
    cache_repo,
    context_service,
    user_memory_service,
    rag_engine,
):
    chat_repo.get_chat.return_value = _make_chat()
    context_service.get_or_load_context.return_value = (
        "previous summary",
        [{"role": "user", "content": "earlier question"}],
    )
    user_memory_service.get_context_for_prompt.return_value = "student memory"
    message_repo.create.side_effect = [USER_MESSAGE_ID, ASSISTANT_MESSAGE_ID]
    rag_engine.ask.return_value = TutorResponse(
        answer="Resposta do tutor.",
        sources=[TutorSource(filename="ed.pdf", pages=[1, 2])],
        is_fallback=False,
    )

    user_msg, assistant_msg, response = await service.send_message(
        CONVERSATION_ID,
        "O que e uma lista ligada?",
        USER_ID,
    )

    chat_repo.get_chat.assert_awaited_once_with(CONVERSATION_ID)
    context_service.get_or_load_context.assert_awaited_once_with(CONVERSATION_ID)
    user_memory_service.get_context_for_prompt.assert_awaited_once_with(USER_ID, ED_ID)
    rag_engine.ask.assert_called_once_with(
        "ed",
        "O que e uma lista ligada?",
        "previous summary",
        [{"role": "user", "content": "earlier question"}],
        "student memory",
    )

    assert user_msg.id == USER_MESSAGE_ID
    assert user_msg.role == Role.user
    assert user_msg.content == "O que e uma lista ligada?"
    assert assistant_msg.id == ASSISTANT_MESSAGE_ID
    assert assistant_msg.role == Role.assistant
    assert assistant_msg.content == "Resposta do tutor."
    assert assistant_msg.sources[0].filename == "ed.pdf"
    assert response.answer == "Resposta do tutor."

    assert message_repo.create.await_count == 2
    cache_repo.add_message.assert_any_await(user_msg)
    cache_repo.add_message.assert_any_await(assistant_msg)
    chat_repo.touch.assert_awaited_once_with(CONVERSATION_ID)
    context_service.check_and_trigger_summary.assert_awaited_once_with(CONVERSATION_ID, USER_ID, ED_ID)


async def test_send_message_unknown_chat_raises_not_found(service, chat_repo):
    chat_repo.get_chat.return_value = None

    with pytest.raises(NotFoundError):
        await service.send_message(CONVERSATION_ID, "Pergunta?", USER_ID)


async def test_send_message_wrong_owner_raises_access_denied(service, chat_repo):
    chat_repo.get_chat.return_value = _make_chat(user_id=OTHER_USER_ID)

    with pytest.raises(AccessDeniedError):
        await service.send_message(CONVERSATION_ID, "Pergunta?", USER_ID)
