from app.backend.repositories.interfaces.report_repository import IReportRepository
from app.backend.repositories.interfaces.message_repository import IMessageRepository
from app.backend.schemas.report.models import Report
from app.backend.services.interfaces.report_service import IReportService
from app.backend.core.exceptions import AccessDeniedError, BadRequestError
from app.backend.repositories.interfaces.chat_repository import IChatRepository

class ReportService(IReportService):
    def __init__(
        self, 
        report_repository: IReportRepository,
        message_repository: IMessageRepository,
        chat_repository: IChatRepository
    ) -> None:
        self.report_repository = report_repository
        self.message_repository = message_repository
        self.chat_repository = chat_repository

    async def create_report(
        self, 
        message_id: str,
        requester_user_id: str
    ) -> bool:
        reported_msg = await self.message_repository.get_message(message_id)
        if not reported_msg:
            raise BadRequestError(message="Mensagem nao encontrada", code="report_error")

        chat = await self.chat_repository.get_chat(reported_msg.conversation_id)
        if not chat or chat.user_id != requester_user_id:
            raise AccessDeniedError(message="Nao tens permissao para reportar mensagens deste chat.")
            
        if reported_msg.role != "assistant":
            raise BadRequestError(
                message="Apenas mensagens de assistente podem ser reportadas",
                code="report_error",
            )

        prev_msg = await self.message_repository.get_previous_message(
            message_id, 
            reported_msg.conversation_id
        )
        
        if not prev_msg or prev_msg.role != "user":
            raise BadRequestError(
                message="Esta resposta não tem uma mensagem de utilizador correspondente",
                code="report_error",
            )

        if await self.report_repository.exists_by_message_id(prev_msg.id):
            return True 

        report = Report(
            conversation_id=reported_msg.conversation_id,
            message_id=prev_msg.id,
            user_content=prev_msg.content,
            assistant_content=reported_msg.content
        )

        success = await self.report_repository.create(report)
        if success:
            await self.message_repository.update_report_status(message_id, True)
            
        return success

    async def delete_report(
        self,
        message_id: str,
        requester_user_id: str
    ) -> bool:
        msg = await self.message_repository.get_message(message_id)
        if not msg:
            raise BadRequestError(message="Mensagem nao encontrada", code="report_error")

        chat = await self.chat_repository.get_chat(msg.conversation_id)
        if not chat or chat.user_id != requester_user_id:
            raise AccessDeniedError(message="Nao tens permissao para remover reports deste chat.")

        prev_msg = await self.message_repository.get_previous_message(
            message_id, 
            msg.conversation_id
        )
        
        target_report_id = prev_msg.id if prev_msg else message_id

        deleted = await self.report_repository.delete_by_message_id(target_report_id)
        
        await self.message_repository.update_report_status(message_id, False)
        
        return deleted
