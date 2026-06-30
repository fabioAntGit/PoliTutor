from unittest.mock import AsyncMock

import pytest
from bson import ObjectId

from app.backend.core.exceptions import AuthError
from app.backend.repositories.interfaces.cache_repository import ICacheRepository
from app.backend.repositories.interfaces.user_repository import IUserRepository
from app.backend.schemas.user.models import User
from app.backend.services.authentication import AuthenticationService
from app.backend.services.interfaces.security_service import ISecurityService

USER_ID = str(ObjectId())


def _make_user(**kwargs) -> User:
    defaults = dict(
        id=USER_ID,
        email="fabio@estg.ipp.pt",
        username="fabio",
        full_name="Fabio Silva",
        role="student",
        hashed_password="hashed_pw",
        courses=[],
        must_change_password=False,
    )
    defaults.update(kwargs)
    return User(**defaults)


@pytest.fixture
def user_repo():
    return AsyncMock(spec=IUserRepository)


@pytest.fixture
def security():
    return AsyncMock(spec=ISecurityService)


@pytest.fixture
def redis_repo():
    return AsyncMock(spec=ICacheRepository)


@pytest.fixture
def service(user_repo, security, redis_repo):
    return AuthenticationService(
        user_repository=user_repo,
        security_service=security,
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


async def test_logout_valid_token_adds_to_blacklist(service, security, redis_repo):
    security.decode_token.return_value = {"exp": 9999999999}

    result = await service.logout("some_token")

    assert result is True
    redis_repo.add_token_to_blacklist.assert_awaited_once()


async def test_logout_expired_token_returns_true(service, security):
    security.decode_token.side_effect = AuthError(message="Token expirado")

    result = await service.logout("expired_token")

    assert result is True
