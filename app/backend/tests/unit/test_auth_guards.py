from unittest.mock import AsyncMock, MagicMock

import pytest

from app.backend.api.deps import _enforce_password_change, require_role
from app.backend.core.exceptions import AccessDeniedError
from app.backend.schemas.user.enums import UserRole
from app.backend.services.interfaces.authentication_service import IAuthenticationService

@pytest.fixture
def auth_service():
    return AsyncMock(spec=IAuthenticationService)


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


async def test_require_role_correct_role_returns_payload(auth_service):
    auth_service.verify_token.return_value = {
        "role": "admin",
        "must_change_password": False,
    }

    guard = require_role(UserRole.ADMIN)
    request = MagicMock()
    request.url.path = "/api/v1/users"

    result = await guard(request=request, token="token", authentication_service=auth_service)

    assert result["role"] == "admin"


async def test_require_role_wrong_role_throws_access_denied_error(auth_service):
    auth_service.verify_token.return_value = {
        "role": "student",
        "must_change_password": False,
    }

    guard = require_role(UserRole.ADMIN)
    request = MagicMock()
    request.url.path = "/api/v1/users"

    with pytest.raises(AccessDeniedError):
        await guard(request=request, token="token", authentication_service=auth_service)
