from app.backend.core.exceptions import AppError


def validate_and_extract_username(email: str) -> str:
    domain = "@estg.ipp.pt"
    if not email.endswith(domain):
        raise AppError(message=f"O email deve pertencer ao dominio {domain}")

    return email.split("@")[0]
