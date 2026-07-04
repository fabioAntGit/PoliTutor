"""OpenRouter LLM client (LangChain wrapper)."""

import logging
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from .config import OPENROUTER_MODEL_GENERATOR
from .interfaces.model_client import IModelClient

load_dotenv()

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterClient(IModelClient):
    def _llm(self, model: str | None, max_tokens: int | None, temperature: float) -> ChatOpenAI:
        return ChatOpenAI(
            model=model or OPENROUTER_MODEL_GENERATOR,
            base_url=OPENROUTER_BASE_URL,
            api_key=os.environ["OPENROUTER_KEY"].strip(),
            max_tokens=max_tokens,
            temperature=temperature,
            max_retries=3,
            timeout=120,
        )

    def call(
        self,
        messages: list[dict],
        max_tokens: int | None = None,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> str | None:
        try:
            return self._llm(model, max_tokens, temperature).invoke(messages).text
        except Exception as e:
            logger.error("[OpenRouter] request failed: %s", e)
            return None

    def call_structured(
        self,
        messages: list[dict],
        schema: type[BaseModel],
        max_tokens: int | None = None,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> BaseModel | None:
        try:
            llm = self._llm(model, max_tokens, temperature)
            return llm.with_structured_output(schema, method="json_schema").invoke(messages)
        except Exception as e:
            logger.error("[OpenRouter] structured request failed: %s", e)
            return None
