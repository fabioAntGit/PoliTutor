from fastapi import APIRouter, Depends, Header
from app.backend.api import deps
from app.backend.schemas.report.response import ReportResponse
from app.backend.services.interfaces.report_service import IReportService
from app.backend.schemas.shared.mongo import PyObjectId
from app.backend.schemas.auth import IAEduBaseHeaders

router = APIRouter()

@router.post("/report/{message_id}", response_model=ReportResponse, status_code=201)
async def create_report(
    message_id: PyObjectId,
    headers: IAEduBaseHeaders = Header(...),
    service: IReportService = Depends(deps.get_report_service)
):
    success = await service.create_report(
        message_id=str(message_id),
        requester_user_id=headers.x_iaedu_channel_id
    )
    return ReportResponse(success=success)

@router.delete("/report/{message_id}", response_model=ReportResponse)
async def delete_report(
    message_id: PyObjectId,
    headers: IAEduBaseHeaders = Header(...),
    service: IReportService = Depends(deps.get_report_service)
):
    success = await service.delete_report(
        message_id=str(message_id),
        requester_user_id=headers.x_iaedu_channel_id
    )
    return ReportResponse(success=success)
