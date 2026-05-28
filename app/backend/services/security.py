import jwt
from datetime import datetime, timedelta, timezone
from pwdlib import PasswordHash

from app.backend.services.interfaces.security_service import ISecurityService
from app.backend.core.exceptions import AuthError
from app.backend.core.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
)

class SecurityService(ISecurityService):
    def __init__(self, password_hash: PasswordHash) -> None:
        self.password_hash = password_hash

    async def hash_password(self, password: str) -> str:
        return self.password_hash.hash(password)

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.password_hash.verify(plain_password, hashed_password)

    async def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    async def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        except jwt.PyJWTError:
            raise AuthError(message="Token invalido ou expirado")
