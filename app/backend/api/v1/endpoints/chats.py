from fastapi import APIRouter, status, Depends

from app.backend.schemas.chat.request import ChatCreate
from app.backend.schemas.chat.response import ChatCreated, ChatRead, ChatListItem
from app.backend.services.interfaces.chat_service import IChatService
from app.backend.api.deps import get_chat_service, require_authenticated, require_role
from app.backend.schemas.user.enums import UserRole

router = APIRouter()


@router.post("/chat", response_model=ChatCreated, status_code=status.HTTP_201_CREATED)
async def create_chat(
    body: ChatCreate,
    payload: dict = Depends(require_role(UserRole.STUDENT)),
    service: IChatService = Depends(get_chat_service)
):
    conversation_id = await service.create_chat(
        course_code=body.course_code,
        user_id=payload["id"],
    )
    return ChatCreated(conversation_id=conversation_id)


@router.get("/chats", response_model=list[ChatListItem])
async def list_chats(
    payload: dict = Depends(require_authenticated),
    service: IChatService = Depends(get_chat_service)
):
    chats = await service.list_user_chats(user_id=payload["id"])
    return [
        ChatListItem(
            conversation_id=str(chat.id),
            course_name=course.name,
            updated_at=chat.updated_at,
        )
        for chat, course in chats
    ]


@router.get("/chat/{conversation_id}", response_model=ChatRead, response_model_by_alias=False)
async def get_chat(
    conversation_id: str,
    payload: dict = Depends(require_authenticated),
    service: IChatService = Depends(get_chat_service)
):
    chat, course, messages = await service.get_chat(
        conversation_id, requester_user_id=payload["id"]
    )
    return ChatRead(
        conversation_id=str(chat.id),
        course_code=course.code,
        course_name=course.name,
        user_id=chat.user_id,
        summary=chat.summary,
        messages=messages,
    )


@router.delete("/chat/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    conversation_id: str,
    payload: dict = Depends(require_authenticated),
    service: IChatService = Depends(get_chat_service)
):
    await service.delete_chat(conversation_id, requester_user_id=payload["id"])
