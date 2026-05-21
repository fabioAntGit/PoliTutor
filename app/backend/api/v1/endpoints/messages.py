from fastapi import APIRouter, Depends

from app.backend.schemas.message.request import MessageSend
from app.backend.schemas.message.response import MessageResponse
from app.backend.services.interfaces.message_service import IMessageService
from app.backend.api.deps import get_message_service, require_authenticated

router = APIRouter()


@router.post("/chat/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    body: MessageSend,
    payload: dict = Depends(require_authenticated),
    service: IMessageService = Depends(get_message_service)
):
    return await service.send_message(
        conversation_id=conversation_id,
        question=body.question,
        user_id=payload["id"],
    )
