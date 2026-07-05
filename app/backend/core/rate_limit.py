import jwt
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.backend.core.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.backend.schemas.shared.api_error import ApiError

GLOBAL_DEFAULT = "60/minute"


def user_key(request: Request) -> str:
    """Bucket requests by authenticated user, falling back to client IP.

    The JWT is decoded straight from the ``Authorization`` header so each user
    gets an independent quota regardless of the IP they connect from. When the
    token is missing or invalid we fall back to the client IP.
    """
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            user_id = payload.get("id")
            if user_id:
                return f"user:{user_id}"
        except jwt.PyJWTError:
            pass
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[GLOBAL_DEFAULT],
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a 429 in the API's standard ``ApiError`` shape, with ``Retry-After``."""
    retry_after = exc.limit.limit.get_expiry()
    error = ApiError(
        code="rate_limit_exceeded",
        message="Demasiados pedidos. Aguarda um momento e tenta novamente.",
        details={"limit": str(exc.limit.limit), "retry_after_seconds": retry_after},
    )
    return JSONResponse(
        status_code=429,
        content=error.model_dump(),
        headers={"Retry-After": str(retry_after)},
    )
