from app.backend.core.exceptions import AppError


def validate_and_extract_username(email: str) -> str:
    base_domain = "ipp.pt"
    username, separator, domain = email.partition("@")
    is_ipp = domain == base_domain or domain.endswith(f".{base_domain}")
    if not separator or not username or not is_ipp:
        raise AppError(message=f"O email deve pertencer ao dominio {base_domain}")

    return username
