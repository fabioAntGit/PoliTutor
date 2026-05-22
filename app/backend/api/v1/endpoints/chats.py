from fastapi import APIRouter, status, Depends

from app.backend.schemas.chat.request import ChatCreate
from app.backend.schemas.chat.response import ChatCreated, ChatRead, ChatListItem
from app.backend.services.interfaces.chat_service import IChatService
from app.backend.api.deps import get_chat_service, require_authenticated

router = APIRouter()


@router.post("/chat", response_model=ChatCreated, status_code=status.HTTP_201_CREATED)
async def create_chat(
    body: ChatCreate,
    payload: dict = Depends(require_authenticated),
    service: IChatService = Depends(get_chat_service)
):
    return await service.create_chat(
        course_code=body.course_code,
        user_id=payload["id"]
    )


@router.get("/chats", response_model=list[ChatListItem])
async def list_chats(
    payload: dict = Depends(require_authenticated),
    service: IChatService = Depends(get_chat_service)
):
    return await service.list_user_chats(user_id=payload["id"])


@router.get("/chat/{conversation_id}", response_model=ChatRead, response_model_by_alias=False)
async def get_chat(
    conversation_id: str,
    payload: dict = Depends(require_authenticated),
    service: IChatService = Depends(get_chat_service)
):
    return await service.get_chat(conversation_id, requester_user_id=payload["id"])
