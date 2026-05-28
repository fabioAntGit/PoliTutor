from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.backend.schemas.auth.response import LoginResponse
from app.backend.schemas.auth.request import LogoutRequest
from app.backend.schemas.user.request import ChangePasswordRequest
from app.backend.services.interfaces.authentication_service import IAuthenticationService
from app.backend.services.interfaces.user_service import IUserService
from app.backend.services.interfaces.security_service import ISecurityService
from app.backend.core.exceptions import AuthError
from app.backend.api.deps import (
    get_authentication_service,
    get_user_service,
    get_security_service,
    require_authenticated,
    oauth2_scheme,
)

router = APIRouter()

@router.post("/auth/login", response_model=LoginResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    service: IAuthenticationService = Depends(get_authentication_service),
):
    access_token = await service.login(
        username=form.username,
        password=form.password,
    )
    return LoginResponse(access_token=access_token)


@router.post("/auth/logout")
async def logout(
    body: LogoutRequest,
    service: IAuthenticationService = Depends(get_authentication_service),
):
    await service.logout(access_token=body.access_token)
    return {"message": "Logout efetuado com sucesso"}


@router.post("/auth/change-password", response_model=LoginResponse)
async def change_password(
    body: ChangePasswordRequest,
    payload: dict = Depends(require_authenticated),
    old_token: str = Depends(oauth2_scheme),
    user_service: IUserService = Depends(get_user_service),
    security_service: ISecurityService = Depends(get_security_service),
    auth_service: IAuthenticationService = Depends(get_authentication_service),
):
    username = payload.get("username")
    if not username:
        raise AuthError(message="Token invalido")

    user = await user_service.change_password(
        username=username,
        current_password=body.current_password,
        new_password=body.new_password,
    )

    await auth_service.logout(access_token=old_token)

    new_payload = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "courses": user.courses,
        "must_change_password": user.must_change_password,
    }
    access_token = await security_service.create_access_token(new_payload)
    return LoginResponse(access_token=access_token)
