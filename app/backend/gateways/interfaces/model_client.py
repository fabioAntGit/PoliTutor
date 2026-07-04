from typing import Protocol, runtime_checkable

from pydantic import BaseModel


@runtime_checkable
class IModelClient(Protocol):
    def call(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> str | None:
        ...

    def call_structured(
        self,
        messages: list[dict],
        schema: type[BaseModel],
        max_tokens: int | None = None,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> BaseModel | None:
        ...
