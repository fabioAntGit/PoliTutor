from unittest.mock import AsyncMock

import pytest

from app.backend.core.exceptions import AuthError
from app.backend.repositories.interfaces.course_repository import ICourseRepository
from app.backend.repositories.interfaces.cache_repository import ICacheRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.schemas.course.models import Course
from app.backend.schemas.user.models import User
from app.backend.services.authentication import AuthenticationService
from app.backend.services.interfaces.security_service import ISecurityService

def _make_user(**kwargs) -> User:
    defaults = dict(
        id="user123",
        email="fabio@estg.ipp.pt",
        username="fabio",
        full_name="Fabio Silva",
        role="student",
        hashed_password="hashed_pw",
        courses=["ed"],
        must_change_password=False,
    )
    defaults.update(kwargs)
    return User(**defaults)


def _make_course(**kwargs) -> Course:
    defaults = dict(code="ed", name="Estruturas de Dados", is_active=True)
    defaults.update(kwargs)
    return Course(**defaults)


@pytest.fixture
def user_repo():
    return AsyncMock(spec=IUserRepository)


@pytest.fixture
def security():
    return AsyncMock(spec=ISecurityService)


@pytest.fixture
def course_repo():
    return AsyncMock(spec=ICourseRepository)


@pytest.fixture
def redis_repo():
    return AsyncMock(spec=ICacheRepository)


@pytest.fixture
def service(user_repo, security, course_repo, redis_repo):
    return AuthenticationService(
        user_repository=user_repo,
        security_service=security,
        course_repository=course_repo,
        cache_repository=redis_repo,
    )


async def test_login_valid_credentials_returns_token(service, user_repo, security):
    user_repo.find_by_username.return_value = _make_user()
    security.verify_password.return_value = True
    security.create_access_token.return_value = "jwt_token_123"

    result = await service.login("fabio", "password123")

    assert result == "jwt_token_123"
    security.verify_password.assert_awaited_once()


async def test_login_user_not_found_throws_auth_error(service, user_repo):
    user_repo.find_by_username.return_value = None

    with pytest.raises(AuthError):
        await service.login("unknown", "password123")


async def test_login_wrong_password_throws_auth_error(service, user_repo, security):
    user_repo.find_by_username.return_value = _make_user()
    security.verify_password.return_value = False

    with pytest.raises(AuthError):
        await service.login("fabio", "wrong_password")


async def test_register_valid_data_returns_true(service, user_repo, security, course_repo):
    user_repo.find_by_username.return_value = None
    user_repo.find_by_email.return_value = None
    course_repo.get_courses_by_codes.return_value = [_make_course()]
    security.hash_password.return_value = "hashed_new_pw"
    user_repo.create.return_value = True

    result = await service.register(
        email="novo@estg.ipp.pt",
        password="password123",
        full_name="Novo User",
        role="student",
        courses=["ed"],
    )

    assert result is True
    security.hash_password.assert_awaited_once_with("password123")
    user_repo.create.assert_awaited_once()


async def test_register_duplicate_username_throws_auth_error(service, user_repo):
    user_repo.find_by_username.return_value = _make_user()

    with pytest.raises(AuthError):
        await service.register(
            email="fabio@estg.ipp.pt",
            password="password123",
            full_name="Fabio",
            role="student",
            courses=[],
        )


async def test_register_duplicate_email_throws_auth_error(service, user_repo):
    user_repo.find_by_username.return_value = None
    user_repo.find_by_email.return_value = _make_user()

    with pytest.raises(AuthError):
        await service.register(
            email="fabio@estg.ipp.pt",
            password="password123",
            full_name="Fabio",
            role="student",
            courses=[],
        )


async def test_register_invalid_courses_throws_auth_error(service, user_repo, course_repo):
    user_repo.find_by_username.return_value = None
    user_repo.find_by_email.return_value = None
    course_repo.get_courses_by_codes.return_value = []

    with pytest.raises(AuthError):
        await service.register(
            email="novo@estg.ipp.pt",
            password="password123",
            full_name="Novo User",
            role="student",
            courses=["cadeira_falsa"],
        )


async def test_register_password_stores_hashed_value(service, user_repo, security, course_repo):
    user_repo.find_by_username.return_value = None
    user_repo.find_by_email.return_value = None
    security.hash_password.return_value = "hashed_value"
    user_repo.create.return_value = True

    await service.register(
        email="teste@estg.ipp.pt",
        password="plaintext_pw",
        full_name="Teste",
        role="student",
        courses=[],
    )

    # Verificar que o hash foi chamado com a password em plaintext
    security.hash_password.assert_awaited_once_with("plaintext_pw")
    # Verificar que o user criado tem a password hashed, nao plaintext
    created_user = user_repo.create.call_args[0][0]
    assert created_user.hashed_password == "hashed_value"


async def test_logout_valid_token_adds_to_blacklist(service, security, redis_repo):
    security.decode_token.return_value = {"exp": 9999999999}

    result = await service.logout("some_token")

    assert result is True
    redis_repo.add_token_to_blacklist.assert_awaited_once()


async def test_logout_expired_token_returns_true(service, security):
    security.decode_token.side_effect = AuthError(message="Token expirado")

    result = await service.logout("expired_token")

    assert result is True
