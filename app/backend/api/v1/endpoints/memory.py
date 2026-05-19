from fastapi import APIRouter, Depends, HTTPException

from app.backend.api.deps import get_user_memory_service
from app.backend.schemas.memory.response import UserMemoryListRead, UserMemoryRead
from app.backend.services.interfaces.user_memory_service import IUserMemoryService

router = APIRouter()


@router.get("/memory/{user_id}", response_model=UserMemoryListRead)
async def list_memories(
    user_id: str,
    course: str,
    service: IUserMemoryService = Depends(get_user_memory_service),
):
    memories = await service.list_memories(user_id, course)
    return UserMemoryListRead(
        memories=[UserMemoryRead(**m.model_dump()) for m in memories],
        total=len(memories),
    )


@router.delete("/memory/{user_id}/{mem_id}", status_code=204)
async def delete_memory(
    user_id: str,
    mem_id: str,
    service: IUserMemoryService = Depends(get_user_memory_service),
):
    deleted = await service.delete_memory(user_id, mem_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found.")
