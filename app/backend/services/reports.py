from app.backend.repositories.reports import ReportRepository
from app.backend.repositories.messages import MessageRepository
from app.backend.schemas.report.models import Report
from app.backend.services.interfaces.report_service import IReportService
from app.backend.core.exceptions import ReportError, AccessDeniedError
from app.backend.repositories.chats import ChatRepository

class ReportService(IReportService):
    def __init__(
        self, 
        repository: ReportRepository,
        message_repository: MessageRepository,
        chat_repository: ChatRepository
    ) -> None:
        self.repository = repository
        self.message_repository = message_repository
        self.chat_repository = chat_repository

    async def create_report(
        self, 
        message_id: str,
        requester_user_id: str
    ) -> bool:
        reported_msg = await self.message_repository.get_message(message_id)
        if not reported_msg:
            raise ReportError(message="Mensagem nao encontrada")

        chat = await self.chat_repository.get_chat(reported_msg.conversation_id)
        if not chat or chat.user_id != requester_user_id:
            raise AccessDeniedError("Nao tens permissao para reportar mensagens deste chat.")
            
        if reported_msg.role != "user":
            raise ReportError(message="Apenas mensagens de utilizador podem ser reportadas")

        next_msg = await self.message_repository.get_next_message(
            message_id, 
            reported_msg.conversation_id
        )
        
        if not next_msg or next_msg.role != "assistant":
            raise ReportError(message="Esta mensagem ainda nao tem uma resposta do assistente")

        if await self.repository.exists_by_message_id(message_id):
            return True 

        report = Report(
            conversation_id=reported_msg.conversation_id,
            message_id=reported_msg.id,
            user_content=reported_msg.content,
            assistant_content=next_msg.content
        )

        success = await self.repository.create(report)
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
            raise ReportError(message="Mensagem nao encontrada")

        # Verify chat ownership
        chat = await self.chat_repository.get_chat(msg.conversation_id)
        if not chat or chat.user_id != requester_user_id:
            raise AccessDeniedError("Nao tens permissao para remover reports deste chat.")

        deleted = await self.repository.delete_by_message_id(message_id)
        
        await self.message_repository.update_report_status(message_id, False)
        
        return deleted