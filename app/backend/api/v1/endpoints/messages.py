import logging

from fastapi import APIRouter, Depends, Header

from app.backend.schemas.message.request import MessageSend, MessageCredentials
from app.backend.schemas.message.response import MessageResponse
from app.backend.services.interfaces.message_service import IMessageService
from app.backend.api.deps import get_message_service

router = APIRouter()


@router.post("/chat/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    body: MessageSend,
    headers: MessageCredentials = Header(...),
    service: IMessageService = Depends(get_message_service)
):
    return await service.send_message(
        conversation_id=conversation_id,
        question=body.question,
        iaedu_api_key=headers.x_iaedu_api_key,
        iaedu_endpoint=headers.x_iaedu_endpoint,
        iaedu_channel_id=headers.x_iaedu_channel_id
    )
