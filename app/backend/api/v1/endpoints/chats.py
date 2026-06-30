from fastapi import APIRouter, status, Depends, Request

from app.backend.core.rate_limit import limiter, user_key
from app.backend.schemas.chat.request import ChatCreate
from app.backend.schemas.chat.response import ChatCreated, ChatRead, ChatListItem
from app.backend.services.interfaces.chat_service import IChatService
from app.backend.schemas.shared.responses import forbidden, not_found, unauthorized
from app.backend.api.deps import get_chat_service, require_authenticated, require_role
from app.backend.schemas.user.enums import UserRole

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new conversation",
    response_description="Identifier of the created conversation.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not a student, or is not enrolled in the course."),
        **not_found("Course does not exist or is inactive."),
    },
)
@limiter.limit("10/minute", key_func=user_key)
async def create_chat(
    request: Request,
    body: ChatCreate,
    payload: dict = Depends(require_role(UserRole.STUDENT)),
    service: IChatService = Depends(get_chat_service)
):
    conversation_id = await service.create_chat(
        course_id=body.course_id,
        user_id=payload["id"],
    )
    return ChatCreated(conversation_id=conversation_id)


@router.get(
    "/chats",
    response_model=list[ChatListItem],
    summary="List the caller's conversations",
    response_description="The caller's conversations, most recently updated first.",
    responses={**unauthorized()},
)
@limiter.limit("30/minute", key_func=user_key)
async def list_chats(
    request: Request,
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


@router.get(
    "/chat/{conversation_id}",
    response_model=ChatRead,
    response_model_by_alias=False,
    summary="Fetch a conversation with its messages",
    response_description="The conversation, its course and full message history.",
    responses={
        **unauthorized(),
        **forbidden("Caller does not own this conversation."),
        **not_found("Conversation or its course does not exist."),
    },
)
@limiter.limit("30/minute", key_func=user_key)
async def get_chat(
    request: Request,
    conversation_id: str,
    payload: dict = Depends(require_authenticated),
    service: IChatService = Depends(get_chat_service)
):
    chat, course, messages = await service.get_chat(
        conversation_id, requester_user_id=payload["id"]
    )
    return ChatRead(
        conversation_id=str(chat.id),
        course_name=course.name,
        messages=messages,
    )


@router.delete(
    "/chat/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation",
    response_description="The conversation and its messages were removed.",
    responses={
        **unauthorized(),
        **forbidden("Caller does not own this conversation."),
        **not_found("Conversation does not exist."),
    },
)
@limiter.limit("10/minute", key_func=user_key)
async def delete_chat(
    request: Request,
    conversation_id: str,
    payload: dict = Depends(require_authenticated),
    service: IChatService = Depends(get_chat_service)
):
    await service.delete_chat(conversation_id, requester_user_id=payload["id"])
