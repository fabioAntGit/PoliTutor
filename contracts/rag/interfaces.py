from typing import Protocol, runtime_checkable

from .models import TutorResponse

@runtime_checkable
class IRagEngine(Protocol):

    def ask(
        self,
        course: str,
        query: str,
        summary: str = "",
        history: list[dict] | None = None,
        memory: str = "",
        course_scope: str = "",
    ) -> TutorResponse:
        ...

    def preload_models(self) -> None:
        ...
