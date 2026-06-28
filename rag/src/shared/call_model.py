"""OpenRouter LLM client."""

import json
import logging
import os
import time

import requests
from dotenv import load_dotenv

from .config import OPENROUTER_MODEL_GENERATOR
from .interfaces.model_client import IModelClient

load_dotenv()

logger = logging.getLogger(__name__)


class OpenRouterClient(IModelClient):
    def call(
        self,
        messages: list[dict],
        max_tokens: int = 1000,
        temperature: float = 0.2,
        model: str | None = None,
        response_format: dict | None = None,
    ) -> str | None:
        model = model or OPENROUTER_MODEL_GENERATOR

        api_key = os.environ["OPENROUTER_KEY"].strip()

        payload: dict = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format is not None:
            payload["response_format"] = response_format

        max_retries = 3
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    data=json.dumps(payload),
                    timeout=(10, 120),
                )
            except requests.RequestException as e:
                logger.error("OpenRouter API request failed: %s", e)
                return None

            if response.status_code == 429:
                logger.warning(
                    "Rate limited (429). Retrying in %ds (attempt %d/%d)...",
                    retry_delay, attempt + 1, max_retries,
                )
                time.sleep(retry_delay)
                retry_delay *= 2
                continue

            if not response.ok:
                logger.error("[OpenRouter] API error %d: %s", response.status_code, response.text[:500])
                return None

            return response.json()["choices"][0]["message"]["content"]

        logger.error("Max retries reached due to rate limiting.")
        return None
