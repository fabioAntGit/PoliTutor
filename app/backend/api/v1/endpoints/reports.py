from fastapi import APIRouter, Depends, Request
from app.backend.api.deps import get_report_service, require_authenticated
from app.backend.core.rate_limit import limiter, user_key
from app.backend.schemas.report.response import ReportResponse
from app.backend.services.interfaces.report_service import IReportService
from app.backend.schemas.shared.mongo import PyObjectId

router = APIRouter()

@router.post("/report/{message_id}", response_model=ReportResponse, status_code=201)
@limiter.limit("10/minute", key_func=user_key)
async def create_report(
    request: Request,
    message_id: PyObjectId,
    payload: dict = Depends(require_authenticated),
    service: IReportService = Depends(get_report_service)
):
    success = await service.create_report(
        message_id=str(message_id),
        requester_user_id=payload["id"]
    )
    return ReportResponse(success=success)

@router.delete("/report/{message_id}", response_model=ReportResponse)
@limiter.limit("10/minute", key_func=user_key)
async def delete_report(
    request: Request,
    message_id: PyObjectId,
    payload: dict = Depends(require_authenticated),
    service: IReportService = Depends(get_report_service)
):
    success = await service.delete_report(
        message_id=str(message_id),
        requester_user_id=payload["id"]
    )
    return ReportResponse(success=success)
