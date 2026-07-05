from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId

from app.backend.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.deletion_repository import IDeletionRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.schemas.course.models import Course
from app.backend.schemas.user.models import User
from app.backend.services.users import UserService

USER_ID = str(ObjectId())
ED_ID = str(ObjectId())
CHAT_ID = str(ObjectId())


def _make_user(**kwargs) -> User:
    defaults = dict(
        id=USER_ID,
        email="fabio@estg.ipp.pt",
        username="fabio",
        full_name="Fabio Silva",
        role="student",
        hashed_password="hashed_pw",
        courses=[],
    )
    defaults.update(kwargs)
    return User(**defaults)


def _make_course() -> Course:
    defaults = dict(_id=ED_ID, code="ed", name="Estruturas de Dados", scope="", is_active=True)
    return Course(**defaults)

@pytest.fixture
def user_repo():
    return AsyncMock(spec=IUserRepository)


@pytest.fixture
def course_repo():
    return AsyncMock(spec=ICourseRepository)


@pytest.fixture
def chat_repo():
    return AsyncMock(spec=IChatRepository)


@pytest.fixture
def deletion_repo():
    return AsyncMock(spec=IDeletionRepository)

@pytest.fixture
def security_service():
    from app.backend.services.interfaces.security_service import ISecurityService
    svc = AsyncMock(spec=ISecurityService)
    svc.hash_password.return_value = "hashed_pw"
    svc.verify_password.return_value = True
    return svc


@pytest.fixture
def service(user_repo, course_repo, chat_repo, deletion_repo, security_service):
    return UserService(
        user_repository=user_repo,
        course_repository=course_repo,
        chat_repository=chat_repo,
        deletion_repository=deletion_repo,
        security_service=security_service,
    )

async def test_create_user_valid_data_returns_user(service, user_repo, course_repo, security_service):
    user_repo.find_by_email.return_value = None
    user_repo.find_by_username.return_value = None
    course_repo.get_courses_by_ids.return_value = [_make_course()]

    result = await service.create_user(
        email="novo@estg.ipp.pt",
        password="password123",
        full_name="Novo User",
        role="student",
        courses=[ED_ID],
    )

    assert result.courses == [ED_ID]

    assert result.username == "novo"
    assert result.email == "novo@estg.ipp.pt"
    assert result.hashed_password == "hashed_pw"
    user_repo.create.assert_awaited_once()
    security_service.hash_password.assert_awaited_once_with("password123")


async def test_create_user_duplicate_email_throws_conflict(service, user_repo):
    user_repo.find_by_email.return_value = _make_user()

    with pytest.raises(ConflictError, match="email"):
        await service.create_user(
            email="fabio@estg.ipp.pt",
            password="password123",
            full_name="Fabio",
            role="student",
            courses=[],
        )

async def test_create_user_duplicate_username_throws_conflict(service, user_repo):
    user_repo.find_by_email.return_value = None
    user_repo.find_by_username.return_value = _make_user(email="fabio@ipp.pt")

    with pytest.raises(ConflictError, match="username"):
        await service.create_user(
            email="fabio@estg.ipp.pt",
            password="password123",
            full_name="Fabio",
            role="student",
            courses=[],
        )


async def test_create_user_invalid_courses_throws_bad_request(service, user_repo, course_repo):
    user_repo.find_by_email.return_value = None
    user_repo.find_by_username.return_value = None
    course_repo.get_courses_by_ids.return_value = []

    with pytest.raises(BadRequestError, match="cadeiras"):
        await service.create_user(
            email="novo@estg.ipp.pt",
            password="password123",
            full_name="Novo",
            role="student",
            courses=[str(ObjectId())],
        )


async def test_update_user_new_email_returns_recalculated_username(service, user_repo):
    user_repo.find_by_username.side_effect = [
        _make_user(),
        None,
    ]
    user_repo.find_by_email.return_value = None

    result = await service.update_user("fabio", {"email": "novo@estg.ipp.pt"})

    assert result.username == "novo"
    user_repo.update.assert_awaited_once()


async def test_update_user_not_found_throws_not_found(service, user_repo):
    user_repo.find_by_username.return_value = None

    with pytest.raises(NotFoundError):
        await service.update_user("nao_existe", {"full_name": "Outro"})


async def test_delete_user_cascades_returns_true(service, user_repo, chat_repo, deletion_repo):
    user_repo.find_by_username.return_value = _make_user()
    chat_repo.get_chats.return_value = [SimpleNamespace(id=CHAT_ID)]

    result = await service.delete_user("fabio")

    assert result is True
    deletion_repo.move_user_related_docs.assert_awaited_once_with(
        user_id=USER_ID,
        username="fabio",
        conversation_ids=[CHAT_ID],
    )


async def test_change_password_valid_data_returns_user(service, user_repo, security_service):
    user_repo.find_by_username.return_value = _make_user(hashed_password="old_hash")
    security_service.verify_password.return_value = True
    security_service.hash_password.return_value = "new_hashed_pw"

    result = await service.change_password(
        username="fabio",
        current_password="current_pw",
        new_password="newpassword123",
    )

    assert result.hashed_password == "new_hashed_pw"
    assert result.must_change_password is False
    user_repo.update.assert_awaited_once()
    security_service.verify_password.assert_awaited_once_with("current_pw", "old_hash")
    security_service.hash_password.assert_awaited_once_with("newpassword123")


async def test_change_password_wrong_current_throws_bad_request(service, user_repo, security_service):
    user_repo.find_by_username.return_value = _make_user(hashed_password="old_hash")
    security_service.verify_password.return_value = False

    with pytest.raises(BadRequestError, match="Password atual incorreta"):
        await service.change_password(
            username="fabio",
            current_password="senha_errada_completamente_diferente",
            new_password="newpassword123",
        )
