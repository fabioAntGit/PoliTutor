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


class ProjectNotFoundError(AppError):
    status_code = 404
    code = "project_not_found"
    message = "Projeto nao encontrado"

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id
        super().__init__(details={"project_id": project_id})


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
