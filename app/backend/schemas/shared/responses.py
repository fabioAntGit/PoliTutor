from app.backend.schemas.shared.api_error import ApiError


def _error(status: int, description: str) -> dict:
    return {status: {"model": ApiError, "description": description}}


def bad_request(description: str = "The request payload failed validation.") -> dict:
    """``400`` — the request was rejected by a domain/validation rule."""
    return _error(400, description)


def unauthorized(description: str = "Missing or invalid authentication token.") -> dict:
    """``401`` — authentication is missing, malformed or expired."""
    return _error(401, description)


def forbidden(description: str = "Caller lacks permission for this resource.") -> dict:
    """``403`` — the caller is authenticated but not allowed."""
    return _error(403, description)


def not_found(description: str = "The requested resource does not exist.") -> dict:
    """``404`` — the target resource could not be found."""
    return _error(404, description)


def conflict(description: str = "The resource conflicts with existing data.") -> dict:
    """``409`` — the request conflicts with the current state."""
    return _error(409, description)
