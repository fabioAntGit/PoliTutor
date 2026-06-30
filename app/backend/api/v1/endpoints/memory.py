from fastapi import APIRouter, Depends, Request

from app.backend.api.deps import get_user_memory_service, require_authenticated
from app.backend.core.exceptions import NotFoundError
from app.backend.core.rate_limit import limiter, user_key
from app.backend.schemas.memory.response import UserMemoryListRead, UserMemoryRead
from app.backend.schemas.shared.mongo import PyObjectId
from app.backend.schemas.shared.responses import not_found, unauthorized
from app.backend.services.interfaces.user_memory_service import IUserMemoryService

router = APIRouter()


@router.get(
    "/memory",
    response_model=UserMemoryListRead,
    summary="List the caller's memories for a course",
    response_description="The caller's stored memories for the given course.",
    responses={**unauthorized()},
)
@limiter.limit("20/minute", key_func=user_key)
async def list_memories(
    request: Request,
    course_id: PyObjectId,
    payload: dict = Depends(require_authenticated),
    service: IUserMemoryService = Depends(get_user_memory_service),
):
    user_id = payload["id"]
    memories = await service.list_memories(user_id, course_id)
    return UserMemoryListRead(
        memories=[
            UserMemoryRead(
                id=m.id,
                type=m.type,
                topic=m.topic,
                content=m.content,
                importance=m.importance,
                last_seen_at=m.last_seen_at,
                created_at=m.created_at,
            )
            for m in memories
        ],
        total=len(memories),
    )


@router.delete(
    "/memory/{mem_id}",
    status_code=204,
    summary="Delete one of the caller's memories",
    response_description="The memory was removed.",
    responses={**unauthorized(), **not_found("Memory does not exist.")},
)
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
        raise NotFoundError(message="Memoria nao encontrada", code="memory_not_found")
