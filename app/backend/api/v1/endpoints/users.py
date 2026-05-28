from fastapi import APIRouter, Depends, status

from app.backend.schemas.user.request import UserCreateRequest, UserUpdateRequest
from app.backend.schemas.user.response import UserResponse
from app.backend.services.interfaces.authentication_service import IAuthenticationService
from app.backend.services.interfaces.user_service import IUserService
from app.backend.core.exceptions import AppError, UserNotFoundError
from app.backend.api.deps import (
    get_authentication_service,
    get_user_service,
    oauth2_scheme,
    require_admin,
    require_authenticated,
)

router = APIRouter()


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    payload: dict = Depends(require_authenticated),
    access_token: str = Depends(oauth2_scheme),
    user_service: IUserService = Depends(get_user_service),
    auth_service: IAuthenticationService = Depends(get_authentication_service),
):
    await user_service.delete_user(payload["username"])
    await auth_service.logout(access_token=access_token)


@router.get("/users", response_model=list[UserResponse], dependencies=[Depends(require_admin)])
async def list_users(
    service: IUserService = Depends(get_user_service),
):
    users = await service.get_users()
    return [UserResponse.model_validate(u.model_dump()) for u in users]


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_user(
    body: UserCreateRequest,
    service: IUserService = Depends(get_user_service),
):
    user = await service.create_user(
        email=body.email,
        password=body.password,
        full_name=body.full_name,
        role=body.role.value,
        courses=body.courses,
    )
    return UserResponse.model_validate(user.model_dump())


@router.get("/users/{username}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def get_user(
    username: str,
    service: IUserService = Depends(get_user_service),
):
    user = await service.get_user(username)
    if not user:
        raise UserNotFoundError()
    return UserResponse.model_validate(user.model_dump())


@router.put("/users/{username}", response_model=UserResponse, dependencies=[Depends(require_admin)])
async def update_user(
    username: str,
    body: UserUpdateRequest,
    service: IUserService = Depends(get_user_service),
):
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise AppError(message="Nenhum campo para atualizar")
    user = await service.update_user(username, update_data)
    return UserResponse.model_validate(user.model_dump())


@router.delete(
    "/users/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_user(
    username: str,
    service: IUserService = Depends(get_user_service),
):
    await service.delete_user(username)
