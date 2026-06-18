from typing import Any


class AppError(Exception):
    status_code = 400
    code = "app_error"
    message = "Application error"

    def __init__(
        self,
        *,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.message
        self.details = details
        super().__init__(self.message)


class CourseNotFoundError(AppError):
    status_code = 404
    code = "course_not_found"
    message = "Cadeira nao encontrada"

    def __init__(self, course_code: str) -> None:
        self.course_code = course_code
        super().__init__(details={"course_code": course_code})


class ChatNotFoundError(AppError):
    status_code = 404
    code = "chat_not_found"
    message = "Chat nao encontrado"

    def __init__(self, conversation_id: str) -> None:
        self.conversation_id = conversation_id
        super().__init__(details={"conversation_id": conversation_id})


class ReportError(AppError):
    status_code = 400
    code = "report_error"
    message = "Erro ao processar o report"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, details=details)


class AccessDeniedError(AppError):
    status_code = 403
    code = "access_denied"
    message = "Acesso negado a este recurso"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message=message)


class AuthError(AppError):
    status_code = 401
    code = "auth_error"
    message = "Credenciais invalidas"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message=message)


class UserNotFoundError(AppError):
    status_code = 404
    code = "user_not_found"
    message = "Utilizador nao encontrado"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message=message)


class MemoryNotFoundError(AppError):
    status_code = 404
    code = "memory_not_found"
    message = "Memoria nao encontrada"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message=message)
