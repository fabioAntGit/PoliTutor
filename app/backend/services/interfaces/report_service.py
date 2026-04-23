from typing import Protocol, runtime_checkable

@runtime_checkable
class IReportService(Protocol):
    async def create_report(
        self,
        message_id: str,
        requester_user_id: str
    ) -> bool:
        ...

    async def delete_report(
        self,
        message_id: str,
        requester_user_id: str
    ) -> bool:
        ...
