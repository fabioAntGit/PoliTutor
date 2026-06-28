from unittest.mock import AsyncMock

import pytest
from pwdlib import PasswordHash

from app.backend.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.backend.repositories.interfaces.chat_repository import IChatRepository
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.deletion_repository import IDeletionRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.schemas.course.models import Course
from app.backend.schemas.user.models import User
from app.backend.services.users import UserService

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


def _make_course() -> Course:
    defaults = dict(code="ed", name="Estruturas de Dados", is_active=True)
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
def service(user_repo, course_repo, chat_repo, deletion_repo):
    return UserService(
        user_repository=user_repo,
        course_repository=course_repo,
        chat_repository=chat_repo,
        deletion_repository=deletion_repo,
    )

async def test_create_user_valid_data_returns_user(service, user_repo, course_repo):
    user_repo.find_by_email.return_value = None
    user_repo.find_by_username.return_value = None
    course_repo.get_courses_by_codes.return_value = [_make_course()]

    result = await service.create_user(
        email="novo@estg.ipp.pt",
        password="password123",
        full_name="Novo User",
        role="student",
        courses=["ed"],
    )

    assert result.username == "novo"
    assert result.email == "novo@estg.ipp.pt"
    # A password nao pode estar em plaintext
    assert result.hashed_password != "password123"
    user_repo.create.assert_awaited_once()


async def test_create_user_short_password_throws_bad_request(service):
    with pytest.raises(BadRequestError, match="pelo menos 8 caracteres"):
        await service.create_user(
            email="novo@estg.ipp.pt",
            password="123",
            full_name="Novo",
            role="student",
            courses=[],
        )


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
    course_repo.get_courses_by_codes.return_value = []

    with pytest.raises(BadRequestError, match="cadeiras"):
        await service.create_user(
            email="novo@estg.ipp.pt",
            password="password123",
            full_name="Novo",
            role="student",
            courses=["cadeira_falsa"],
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
    chat_repo.get_chats.return_value = []

    result = await service.delete_user("fabio")

    assert result is True
    # Deve mover os docs de chats, user_memory e users
    assert deletion_repo.move_docs.await_count >= 3


async def test_change_password_valid_data_returns_user(service, user_repo):
    ph = PasswordHash.recommended()
    real_hash = ph.hash("current_pw")
    user_repo.find_by_username.return_value = _make_user(hashed_password=real_hash)

    result = await service.change_password(
        username="fabio",
        current_password="current_pw",
        new_password="newpassword123",
    )

    assert result.hashed_password != real_hash
    assert result.must_change_password is False
    user_repo.update.assert_awaited_once()


async def test_change_password_wrong_current_throws_bad_request(service, user_repo):
    ph = PasswordHash.recommended()
    real_hash = ph.hash("current_pw")
    user_repo.find_by_username.return_value = _make_user(hashed_password=real_hash)

    with pytest.raises(BadRequestError, match="Password atual incorreta"):
        await service.change_password(
            username="fabio",
            current_password="senha_errada_completamente_diferente",
            new_password="newpassword123",
        )


async def test_change_password_new_too_short_throws_bad_request(service, user_repo):
    ph = PasswordHash.recommended()
    real_hash = ph.hash("current_pw")
    user_repo.find_by_username.return_value = _make_user(hashed_password=real_hash)

    with pytest.raises(BadRequestError, match="pelo menos 8 caracteres"):
        await service.change_password(
            username="fabio",
            current_password="current_pw",
            new_password="123",
        )
