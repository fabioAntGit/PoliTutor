from fastapi import APIRouter, Response, status, Depends, Header

from app.backend.schemas.chat.request import ChatCreate
from app.backend.schemas.chat.response import ChatCreated, ChatRead
from app.backend.schemas.auth import IAEduBaseHeaders
from app.backend.services.interfaces.chat_service import IChatService
from app.backend.api.deps import get_chat_service

router = APIRouter()


@router.post("/chat", response_model=ChatCreated, status_code=status.HTTP_201_CREATED)
async def create_chat(
    body: ChatCreate, 
    response: Response,
    headers: IAEduBaseHeaders = Header(...),
    service: IChatService = Depends(get_chat_service)
):
    chat_created, created = await service.create_chat(
        project_id=body.project_id, 
        user_id=headers.x_iaedu_channel_id
    )
    
    if not created:
        response.status_code = status.HTTP_200_OK
        
    return chat_created


@router.get("/chat/{conversation_id}", response_model=ChatRead, response_model_by_alias=False)
async def get_chat(
    conversation_id: str,
    headers: IAEduBaseHeaders = Header(...),
    service: IChatService = Depends(get_chat_service)
):
    return await service.get_chat(conversation_id, requester_user_id=headers.x_iaedu_channel_id)
