from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId

from app.backend.core.exceptions import (
    AccessDeniedError,
    NotFoundError,
)
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.schemas.chat.models import Chat
from app.backend.schemas.course.models import Course
from app.backend.schemas.message.models import Message
from app.backend.schemas.user.models import User
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.repositories.interfaces.report_repository import IReportRepository
from app.backend.services.chats import ChatService

USER_ID = str(ObjectId())
OTHER_USER_ID = str(ObjectId())
ED_ID = str(ObjectId())
PAW_ID = str(ObjectId())
CHAT_ID = "60d5ecb8b4259b3a0c4f1a01"


def _make_course(**kwargs) -> Course:
    defaults = dict(_id=ED_ID, code="ed", name="Estruturas de Dados", scope="", is_active=True)
    defaults.update(kwargs)
    return Course(**defaults)


def _make_user(**kwargs) -> User:
    defaults = dict(
        id=USER_ID,
        email="fabio@estg.ipp.pt",
        username="fabio",
        full_name="Fabio Silva",
        role="student",
        hashed_password="hashed_pw",
        courses=[ED_ID],
    )
    defaults.update(kwargs)
    return User(**defaults)


def _make_chat(**kwargs) -> Chat:
    defaults = dict(
        _id=CHAT_ID,
        course_id=ED_ID,
        user_id=USER_ID,
        summary=None,
    )
    defaults.update(kwargs)
    return Chat(**defaults)


def _make_message(**kwargs) -> Message:
    defaults = dict(
        conversation_id=CHAT_ID,
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
def report_repo():
    return AsyncMock(spec=IReportRepository)


@pytest.fixture
def service(chat_repo, course_repo, user_repo, message_repo, report_repo):
    return ChatService(
        chat_repository=chat_repo,
        course_repository=course_repo,
        user_repository=user_repo,
        message_repository=message_repo,
        report_repository=report_repo,
    )


async def test_create_chat_valid_data_returns_conversation_id(service, course_repo, user_repo, chat_repo):
    course_repo.find_by_id.return_value = _make_course()
    user_repo.find_by_id.return_value = _make_user()
    chat_repo.create.return_value = "new_chat_id"

    result = await service.create_chat(ED_ID, USER_ID)

    assert result == "new_chat_id"
    chat_repo.create.assert_awaited_once()


async def test_create_chat_course_not_found_throws_not_found(service, course_repo):
    course_repo.find_by_id.return_value = None

    with pytest.raises(NotFoundError):
        await service.create_chat(str(ObjectId()), USER_ID)


async def test_create_chat_course_inactive_throws_not_found(service, course_repo):
    course_repo.find_by_id.return_value = _make_course(is_active=False)

    with pytest.raises(NotFoundError):
        await service.create_chat(ED_ID, USER_ID)


async def test_create_chat_user_not_found_throws_not_found(service, course_repo, user_repo):
    course_repo.find_by_id.return_value = _make_course()
    user_repo.find_by_id.return_value = None

    with pytest.raises(NotFoundError):
        await service.create_chat(ED_ID, USER_ID)


async def test_create_chat_user_not_enrolled_throws_access_denied_error(service, course_repo, user_repo):
    course_repo.find_by_id.return_value = _make_course()
    # User is not enrolled in course "ed"
    user_repo.find_by_id.return_value = _make_user(courses=[PAW_ID])

    with pytest.raises(AccessDeniedError):
        await service.create_chat(ED_ID, USER_ID)


async def test_get_chat_owner_returns_chat_data(service, chat_repo, course_repo, message_repo):
    chat_repo.get_chat.return_value = _make_chat()
    course_repo.find_by_id.return_value = _make_course()
    message_repo.get_messages.return_value = [_make_message()]

    chat, course, messages = await service.get_chat(CHAT_ID, USER_ID)

    assert str(chat.id) == CHAT_ID
    assert course.id == ED_ID
    assert course.name == "Estruturas de Dados"
    assert len(messages) == 1
    assert messages[0].content == "Olá tutor!"


async def test_get_chat_not_found_throws_not_found(service, chat_repo):
    chat_repo.get_chat.return_value = None

    with pytest.raises(NotFoundError):
        await service.get_chat("60d5ecb8b4259b3a0c4f1a05", USER_ID)


async def test_get_chat_wrong_user_id_throws_access_denied_error(service, chat_repo):
    chat_repo.get_chat.return_value = _make_chat(user_id=USER_ID)

    with pytest.raises(AccessDeniedError):
        await service.get_chat(CHAT_ID, OTHER_USER_ID)


async def test_list_user_chats_returns_sorted_by_most_recent(service, chat_repo, course_repo):
    now = datetime.now(timezone.utc)
    old = datetime(2024, 1, 1, tzinfo=timezone.utc)

    chat_repo.get_chats.return_value = [
        _make_chat(_id="60d5ecb8b4259b3a0c4f1a02", course_id=ED_ID, updated_at=old),
        _make_chat(_id="60d5ecb8b4259b3a0c4f1a03", course_id=ED_ID, updated_at=now),
    ]
    course_repo.get_courses_by_ids.return_value = [_make_course()]

    result = await service.list_user_chats(USER_ID)

    assert len(result) == 2
    assert str(result[0][0].id) == "60d5ecb8b4259b3a0c4f1a03"
    assert str(result[1][0].id) == "60d5ecb8b4259b3a0c4f1a02"


async def test_list_user_chats_inactive_courses_returns_filtered(service, chat_repo, course_repo):
    chat_repo.get_chats.return_value = [
        _make_chat(_id="60d5ecb8b4259b3a0c4f1a01", course_id=ED_ID),
        _make_chat(_id="60d5ecb8b4259b3a0c4f1a04", course_id=PAW_ID),
    ]
    # Only course "ed" is active, so the "paw" chat must not appear.
    course_repo.get_courses_by_ids.return_value = [_make_course()]

    result = await service.list_user_chats(USER_ID)

    assert len(result) == 1
    assert str(result[0][0].id) == "60d5ecb8b4259b3a0c4f1a01"


async def test_delete_chat_owner_deletes_reports_messages_and_chat(
    service, chat_repo, message_repo, report_repo
):
    chat_repo.get_chat.return_value = _make_chat(user_id=USER_ID)

    await service.delete_chat(CHAT_ID, requester_user_id=USER_ID)

    report_repo.delete_by_conversation.assert_awaited_once_with(CHAT_ID)
    message_repo.delete_by_conversation.assert_awaited_once_with(CHAT_ID)
    chat_repo.delete.assert_awaited_once_with(CHAT_ID)


async def test_delete_chat_not_found_throws_and_deletes_nothing(
    service, chat_repo, message_repo, report_repo
):
    chat_repo.get_chat.return_value = None

    with pytest.raises(NotFoundError):
        await service.delete_chat("60d5ecb8b4259b3a0c4f1a05", requester_user_id=USER_ID)

    report_repo.delete_by_conversation.assert_not_awaited()
    message_repo.delete_by_conversation.assert_not_awaited()
    chat_repo.delete.assert_not_awaited()


async def test_delete_chat_wrong_user_throws_and_deletes_nothing(
    service, chat_repo, message_repo, report_repo
):
    chat_repo.get_chat.return_value = _make_chat(user_id=USER_ID)

    with pytest.raises(AccessDeniedError):
        await service.delete_chat(CHAT_ID, requester_user_id=OTHER_USER_ID)

    report_repo.delete_by_conversation.assert_not_awaited()
    message_repo.delete_by_conversation.assert_not_awaited()
    chat_repo.delete.assert_not_awaited()
