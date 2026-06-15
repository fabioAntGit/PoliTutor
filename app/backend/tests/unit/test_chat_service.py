from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from app.backend.core.exceptions import (
    AccessDeniedError,
    ChatNotFoundError,
    CourseNotFoundError,
    UserNotFoundError,
)
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.schemas.chat.models import Chat
from app.backend.schemas.course.models import Course
from app.backend.schemas.message.models import Message
from app.backend.schemas.user.models import User
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.services.chats import ChatService


def _make_course(**kwargs) -> Course:
    defaults = dict(code="ed", name="Estruturas de Dados", is_active=True)
    defaults.update(kwargs)
    return Course(**defaults)


def _make_user(**kwargs) -> User:
    defaults = dict(
        id="user1",
        email="fabio@estg.ipp.pt",
        username="fabio",
        full_name="Fabio Silva",
        role="student",
        hashed_password="hashed_pw",
        courses=["ed"],
    )
    defaults.update(kwargs)
    return User(**defaults)


def _make_chat(**kwargs) -> Chat:
    defaults = dict(
        _id="60d5ecb8b4259b3a0c4f1a01",
        course="ed",
        user_id="user1",
        summary=None,
    )
    defaults.update(kwargs)
    return Chat(**defaults)


def _make_message(**kwargs) -> Message:
    defaults = dict(
        conversation_id="60d5ecb8b4259b3a0c4f1a01",
        role="user",
        content="Olá tutor!",
    )
    defaults.update(kwargs)
    return Message(**defaults)


@pytest.fixture
def chat_repo():
    return AsyncMock(spec=IChatRepository)


@pytest.fixture
def course_repo():
    return AsyncMock(spec=ICourseRepository)


@pytest.fixture
def user_repo():
    return AsyncMock(spec=IUserRepository)


@pytest.fixture
def message_repo():
    return AsyncMock(spec=IMessageRepository)


@pytest.fixture
def service(chat_repo, course_repo, user_repo, message_repo):
    return ChatService(
        chat_repository=chat_repo,
        course_repository=course_repo,
        user_repository=user_repo,
        message_repository=message_repo,
    )


async def test_create_chat_valid_data_returns_conversation_id(service, course_repo, user_repo, chat_repo):
    course_repo.find_by_code.return_value = _make_course()
    user_repo.find_by_id.return_value = _make_user()
    chat_repo.create.return_value = "new_chat_id"

    result = await service.create_chat("ed", "user1")

    assert result == "new_chat_id"
    chat_repo.create.assert_awaited_once()


async def test_create_chat_course_not_found_throws_course_not_found_error(service, course_repo):
    course_repo.find_by_code.return_value = None

    with pytest.raises(CourseNotFoundError):
        await service.create_chat("cadeira_falsa", "user1")


async def test_create_chat_course_inactive_throws_course_not_found_error(service, course_repo):
    course_repo.find_by_code.return_value = _make_course(is_active=False)

    with pytest.raises(CourseNotFoundError):
        await service.create_chat("ed", "user1")


async def test_create_chat_user_not_found_throws_user_not_found_error(service, course_repo, user_repo):
    course_repo.find_by_code.return_value = _make_course()
    user_repo.find_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await service.create_chat("ed", "user_invalido")


async def test_create_chat_user_not_enrolled_throws_access_denied_error(service, course_repo, user_repo):
    course_repo.find_by_code.return_value = _make_course()
    # User nao tem a cadeira "ed" na lista de courses
    user_repo.find_by_id.return_value = _make_user(courses=["paw"])

    with pytest.raises(AccessDeniedError):
        await service.create_chat("ed", "user1")


async def test_get_chat_owner_returns_chat_data(service, chat_repo, course_repo, message_repo):
    chat_repo.get_chat.return_value = _make_chat()
    course_repo.find_by_code.return_value = _make_course()
    message_repo.get_messages.return_value = [_make_message()]

    chat, course, messages = await service.get_chat("60d5ecb8b4259b3a0c4f1a01", "user1")

    assert str(chat.id) == "60d5ecb8b4259b3a0c4f1a01"
    assert course.code == "ed"
    assert course.name == "Estruturas de Dados"
    assert len(messages) == 1
    assert messages[0].content == "Olá tutor!"


async def test_get_chat_not_found_throws_chat_not_found_error(service, chat_repo):
    chat_repo.get_chat.return_value = None

    with pytest.raises(ChatNotFoundError):
        await service.get_chat("60d5ecb8b4259b3a0c4f1a05", "user1")


async def test_get_chat_wrong_user_id_throws_access_denied_error(service, chat_repo):
    chat_repo.get_chat.return_value = _make_chat(user_id="user1")

    with pytest.raises(AccessDeniedError):
        await service.get_chat("60d5ecb8b4259b3a0c4f1a01", "outro_user")


async def test_list_user_chats_returns_sorted_by_most_recent(service, chat_repo, course_repo):
    now = datetime.now(timezone.utc)
    old = datetime(2024, 1, 1, tzinfo=timezone.utc)

    chat_repo.get_chats.return_value = [
        _make_chat(_id="60d5ecb8b4259b3a0c4f1a02", course="ed", updated_at=old),
        _make_chat(_id="60d5ecb8b4259b3a0c4f1a03", course="ed", updated_at=now),
    ]
    course_repo.get_courses_by_codes.return_value = [_make_course()]

    result = await service.list_user_chats("user1")

    assert len(result) == 2
    assert str(result[0][0].id) == "60d5ecb8b4259b3a0c4f1a03"
    assert str(result[1][0].id) == "60d5ecb8b4259b3a0c4f1a02"


async def test_list_user_chats_inactive_courses_returns_filtered(service, chat_repo, course_repo):
    chat_repo.get_chats.return_value = [
        _make_chat(_id="60d5ecb8b4259b3a0c4f1a01", course="ed"),
        _make_chat(_id="60d5ecb8b4259b3a0c4f1a04", course="paw"),
    ]
    # Se so a cadeira "ed" estiver ativa, "paw" nao deve aparecer
    course_repo.get_courses_by_codes.return_value = [_make_course(code="ed")]

    result = await service.list_user_chats("user1")

    assert len(result) == 1
    assert str(result[0][0].id) == "60d5ecb8b4259b3a0c4f1a01"
