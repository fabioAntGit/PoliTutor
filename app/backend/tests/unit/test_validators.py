import pytest

from app.backend.core.exceptions import AppError
from app.backend.core.validators import validate_and_extract_username


def test_validate_email_valid_estg_returns_username():
    result = validate_and_extract_username("8230365@estg.ipp.pt")
    assert result == "8230365"


def test_validate_email_invalid_domain_throws_app_error():
    with pytest.raises(AppError, match="dominio"):
        validate_and_extract_username("fabio@gmail.com")


def test_validate_email_other_ipp_subdomain_returns_username():
    result = validate_and_extract_username("fabio@isep.ipp.pt")
    assert result == "fabio"


def test_validate_email_bare_ipp_domain_returns_username():
    result = validate_and_extract_username("fabio@ipp.pt")
    assert result == "fabio"


def test_validate_email_missing_at_throws_app_error():
    with pytest.raises(AppError, match="dominio"):
        validate_and_extract_username("estg.ipp.pt")
