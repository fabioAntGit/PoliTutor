from fastapi import APIRouter, Depends, Request

from app.backend.api.deps import get_user_memory_service, require_authenticated
from app.backend.core.exceptions import MemoryNotFoundError
from app.backend.core.rate_limit import limiter, user_key
from app.backend.schemas.memory.response import UserMemoryListRead, UserMemoryRead
from app.backend.services.interfaces.user_memory_service import IUserMemoryService

router = APIRouter()


@router.get("/memory", response_model=UserMemoryListRead)
@limiter.limit("20/minute", key_func=user_key)
async def list_memories(
    request: Request,
    course: str,
    payload: dict = Depends(require_authenticated),
    service: IUserMemoryService = Depends(get_user_memory_service),
):
    user_id = payload["id"]
    memories = await service.list_memories(user_id, course)
    return UserMemoryListRead(
        memories=[UserMemoryRead.model_validate(m.model_dump()) for m in memories],
        total=len(memories),
    )


@router.delete("/memory/{mem_id}", status_code=204)
@limiter.limit("10/minute", key_func=user_key)
async def delete_memory(
    request: Request,
    mem_id: str,
    payload: dict = Depends(require_authenticated),
    service: IUserMemoryService = Depends(get_user_memory_service),
):
    user_id = payload["id"]
    deleted = await service.delete_memory(user_id, mem_id)
    if not deleted:
        raise MemoryNotFoundError()
