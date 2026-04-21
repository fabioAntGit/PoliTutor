"""
Model API Clients.

Provides reusable functions to send prompts to supported LLM backends:
    - call_iaedu:      IAEdu streaming API (multipart POST).
    - call_openrouter: OpenRouter chat completions API.
"""

import json
import logging
import os
import time
import uuid

import requests
from dotenv import load_dotenv

from .config import OPENROUTER_MODEL_GENERATOR

load_dotenv()

logger = logging.getLogger(__name__)


def call_iaedu(
    prompt: str,
    url: str | None = None,
    channel_id: str | None = None,
    api_key: str | None = None,
) -> str | None:
    """
    Sends a prompt to the IAEdu API and returns the response content.

    Uses a unique thread_id per call so each invocation is independent.
    Streams the response and parses the first message event found.

    Credentials can be passed explicitly (per-request, from student frontend)
    or fall back to environment variables (for benchmarks/dev).

    Args:
        prompt:     The full prompt to send to the LLM.
        url:        IAEdu API endpoint. Defaults to IAEDU_API_ENDPOINT env var.
        channel_id: IAEdu channel ID. Defaults to IAEDU_API_CHANNEL env var.
        api_key:    IAEdu API key. Defaults to IAEDU_API_KEY env var.

    Returns:
        The text content of the model's response, or None on failure.
    """
    url = url or os.getenv("IAEDU_API_ENDPOINT")
    channel_id = channel_id or os.getenv("IAEDU_API_CHANNEL")
    api_key = api_key or os.getenv("IAEDU_API_KEY")

    if not all([url, channel_id, api_key]):
        logger.error("IAEdu credentials are not configured (neither passed nor set in environment).")
        return None

    thread_id = uuid.uuid4().hex[:20]

    files = {
        "channel_id": (None, channel_id),
        "thread_id": (None, thread_id),
        "user_info": (None, "{}"),
        "message": (None, prompt),
    }
    headers = {"x-api-key": api_key}

    try:
        response = requests.post(url, files=files, headers=headers, timeout=60)
    except requests.RequestException as e:
        logger.error("IAEdu API request failed: %s", e)
        return None

    if not response.ok:
        logger.error("[IAEDU] API error %d: %s", response.status_code, response.text[:500])
        return None

    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                if data.get("type") == "message":
                    return data["content"]["content"]
                elif data.get("type") == "error":
                    logger.error("[IAEDU] API returned error event: %s", data.get("content", "unknown error"))
                    return None
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                logger.debug("[IAEDU] Could not parse line: %s", exc)
                continue

    logger.warning("[IAEDU] No parseable 'message' event found in response stream.")
    return None


def call_openrouter(prompt: str, max_tokens: int = 1000, model: str | None = None) -> str | None:
    """
    Sends a prompt to the OpenRouter chat completions API and returns the response.

    Retries up to 3 times with exponential backoff on HTTP 429 (rate limit).

    Args:
        prompt:      The full prompt to send to the LLM.
        max_tokens:  Maximum tokens in the response.
        temperature: Sampling temperature.
        model:       OpenRouter model ID. Defaults to OPENROUTER_MODEL_GENERATOR.

    Returns:
        The text content of the model's response, or None on failure.
    """
    model = model or OPENROUTER_MODEL_GENERATOR
    api_key = (os.getenv("OPENROUTER_KEY") or "").strip()
    if not api_key:
        logger.error("OPENROUTER_KEY environment variable is not set.")
        return None
    logger.debug("OPENROUTER_KEY loaded: %s...%s (len=%d)", api_key[:8], api_key[-4:], len(api_key))

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
                data=json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                }),
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

        # log dos usos
        resp_json = response.json()
        usage = resp_json.get("usage", {})

        total_cost = usage.get("cost", 0)

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)

        logger.info(
            "[OpenRouter Usage] Model: %s | Tokens: %d prompt, %d completion (%d total) | Est. Cost: $%f",
            model, prompt_tokens, completion_tokens, total_tokens, total_cost
        )

        return response.json()["choices"][0]["message"]["content"]

    logger.error("Max retries reached due to rate limiting.")
    return None