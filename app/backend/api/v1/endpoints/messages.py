from fastapi import APIRouter, Depends, Request

from app.backend.core.rate_limit import limiter, user_key
from app.backend.schemas.message.request import MessageSend
from app.backend.schemas.message.response import MessageResponse
from app.backend.schemas.shared.responses import forbidden, not_found, unauthorized
from app.backend.services.interfaces.message_service import IMessageService
from app.backend.api.deps import get_message_service, require_role
from app.backend.schemas.user.enums import UserRole

router = APIRouter()


@router.post(
    "/chat/{conversation_id}/messages",
    response_model=MessageResponse,
    summary="Send a question and receive the tutor's answer",
    response_description="The stored user and assistant messages plus the tutor's answer.",
    responses={
        **unauthorized(),
        **forbidden("Caller is not a student, or does not own this conversation."),
        **not_found("Conversation does not exist."),
    },
)
@limiter.limit("10/minute", key_func=user_key)
async def send_message(
    request: Request,
    conversation_id: str,
    body: MessageSend,
    payload: dict = Depends(require_role(UserRole.STUDENT)),
    service: IMessageService = Depends(get_message_service)
):
    user_msg, assistant_msg, response = await service.send_message(
        conversation_id=conversation_id,
        question=body.question,
        user_id=payload["id"],
    )
    return MessageResponse(
        user_message_id=str(user_msg.id),
        assistant_message_id=str(assistant_msg.id),
        answer=response.answer,
        sources=assistant_msg.sources,
        is_fallback=response.is_fallback,
    )
