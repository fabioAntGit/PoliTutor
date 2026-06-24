from typing import Protocol, runtime_checkable


@runtime_checkable
class IModelClient(Protocol):
    """Port for a chat-completions LLM client."""

    def call(
        self,
        messages: list[dict],
        max_tokens: int = 1000,
        temperature: float = 0.2,
        model: str | None = None,
        response_format: dict | None = None,
    ) -> str | None:
        """Send chat messages and return the completion text, or None on failure."""
        ...
