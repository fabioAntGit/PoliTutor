from datetime import timedelta

import pytest
from pwdlib import PasswordHash

from app.backend.core.exceptions import AuthError
from app.backend.services.security import SecurityService


@pytest.fixture
def service():
    return SecurityService(password_hash=PasswordHash.recommended())

async def test_hash_password_returns_hashed_string(service):
    hashed = await service.hash_password("mypassword")
    assert hashed != "mypassword"
    assert len(hashed) > 20


async def test_verify_password_correct_returns_true(service):
    hashed = await service.hash_password("secret123")
    result = await service.verify_password("secret123", hashed)
    assert result is True


async def test_verify_password_wrong_returns_false(service):
    hashed = await service.hash_password("secret123")
    result = await service.verify_password("wrongpassword", hashed)
    assert result is False


async def test_create_access_token_returns_string(service):
    token = await service.create_access_token({"sub": "user1"})
    assert isinstance(token, str)
    assert len(token) > 0


async def test_create_access_token_contains_payload(service):
    payload = {"id": "123", "username": "fabio", "role": "student"}
    token = await service.create_access_token(payload)
    decoded = await service.decode_token(token)

    assert decoded["id"] == "123"
    assert decoded["username"] == "fabio"
    assert decoded["role"] == "student"


async def test_create_access_token_has_expiration(service):
    token = await service.create_access_token({"sub": "user1"})
    decoded = await service.decode_token(token)
    assert "exp" in decoded


async def test_decode_token_expired_throws_auth_error(service):
    token = await service.create_access_token(
        {"sub": "user1"},
        expires_delta=timedelta(seconds=-1),
    )
    with pytest.raises(AuthError):
        await service.decode_token(token)


async def test_decode_token_invalid_throws_auth_error(service):
    with pytest.raises(AuthError):
        await service.decode_token("token.invalido.qualquer")
