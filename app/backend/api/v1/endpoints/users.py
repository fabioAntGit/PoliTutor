from fastapi import APIRouter, Depends, status

from app.backend.schemas.user.request import UserCreateRequest, UserUpdateRequest
from app.backend.schemas.user.response import UserResponse
from app.backend.services.interfaces.user_service import IUserService
from app.backend.core.exceptions import AppError, UserNotFoundError
from app.backend.api.deps import get_user_service, require_admin

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    service: IUserService = Depends(get_user_service),
):
    users = await service.get_users()
    return [UserResponse.model_validate(u.model_dump()) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("/users/{username}", response_model=UserResponse)
async def get_user(
    username: str,
    service: IUserService = Depends(get_user_service),
):
    user = await service.get_user(username)
    if not user:
        raise UserNotFoundError()
    return UserResponse.model_validate(user.model_dump())


@router.put("/users/{username}", response_model=UserResponse)
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


@router.delete("/users/{username}", status_code=status.HTTP_200_OK)
async def delete_user(
    username: str,
    service: IUserService = Depends(get_user_service),
):
    await service.delete_user(username)
    return {"message": "Utilizador desativado com sucesso"}
