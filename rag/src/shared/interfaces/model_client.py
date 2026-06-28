"""LLM client contract."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class IModelClient(Protocol):
    def call(
        self,
        messages: list[dict],
        max_tokens: int = 1000,
        temperature: float = 0.2,
        model: str | None = None,
        response_format: dict | None = None,
    ) -> str | None:
        """Return the model's text reply, or None on API failure/rate-limit."""
        ...
