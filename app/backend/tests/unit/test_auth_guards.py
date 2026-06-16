from unittest.mock import AsyncMock, MagicMock

import pytest

from app.backend.api.deps import _verify_token, _enforce_password_change, require_role
from app.backend.core.exceptions import AuthError, AccessDeniedError
from app.backend.repositories.interfaces.cache_repository import ICacheRepository
from app.backend.schemas.user.enums import UserRole
from app.backend.services.interfaces.security_service import ISecurityService

@pytest.fixture
def security():
    return AsyncMock(spec=ISecurityService)


@pytest.fixture
def redis_repo():
    return AsyncMock(spec=ICacheRepository)


async def test_verify_token_valid_returns_payload(security, redis_repo):
    redis_repo.is_token_blacklisted.return_value = False
    security.decode_token.return_value = {"username": "fabio"}

    result = await _verify_token("valid_token", security, redis_repo)

    assert result["username"] == "fabio"


async def test_verify_token_blacklisted_throws_auth_error(security, redis_repo):
    redis_repo.is_token_blacklisted.return_value = True

    with pytest.raises(AuthError):
        await _verify_token("blacklisted_token", security, redis_repo)


def test_enforce_password_change_flag_true_throws_access_denied_error():
    payload = {"must_change_password": True}
    request = MagicMock()
    request.url.path = "/api/v1/chats"

    with pytest.raises(AccessDeniedError):
        _enforce_password_change(payload, request)


def test_enforce_password_change_change_password_route_passes():
    payload = {"must_change_password": True}
    request = MagicMock()
    request.url.path = "/api/v1/auth/change-password"

    _enforce_password_change(payload, request)


def test_enforce_password_change_flag_false_passes():
    payload = {"must_change_password": False}
    request = MagicMock()
    request.url.path = "/api/v1/chats"

    _enforce_password_change(payload, request)


async def test_require_role_correct_role_returns_payload(security, redis_repo):
    redis_repo.is_token_blacklisted.return_value = False
    security.decode_token.return_value = {
        "role": "admin",
        "must_change_password": False,
    }

    guard = require_role(UserRole.ADMIN)
    request = MagicMock()
    request.url.path = "/api/v1/users"

    result = await guard(request=request, token="token", security_service=security, cache_repository=redis_repo)

    assert result["role"] == "admin"


async def test_require_role_wrong_role_throws_access_denied_error(security, redis_repo):
    redis_repo.is_token_blacklisted.return_value = False
    security.decode_token.return_value = {
        "role": "student",
        "must_change_password": False,
    }

    guard = require_role(UserRole.ADMIN)
    request = MagicMock()
    request.url.path = "/api/v1/users"

    with pytest.raises(AccessDeniedError):
        await guard(request=request, token="token", security_service=security, cache_repository=redis_repo)
