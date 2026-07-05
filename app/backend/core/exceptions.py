from typing import Any


class AppError(Exception):
    status_code = 400
    code = "app_error"
    message = "Application error"

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.details = details
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    code = "bad_request"
    message = "Pedido invalido"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "Recurso nao encontrado"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "Conflito com o estado atual do recurso"


class AccessDeniedError(AppError):
    status_code = 403
    code = "access_denied"
    message = "Acesso negado a este recurso"


class AuthError(AppError):
    status_code = 401
    code = "auth_error"
    message = "Credenciais invalidas"
