"""
IAEdu API Client.

Provides a reusable function to send prompts to the IAEdu LLM endpoint
and parse the streamed response. Used by benchmark generation and the
tutor generator.
"""

import logging
import os
import uuid

import requests

logger = logging.getLogger(__name__)

def call_iaedu(prompt: str) -> str | None:
    """
    Sends a prompt to the IAEdu API and returns the response content.

    Uses a unique thread_id per call so each invocation is independent.
    Streams the response and parses the first message event found.

    Args:
        prompt: The full prompt to send to the LLM.

    Returns:
        The text content of the model's response, or None on failure.
    """
    url = os.getenv("IAEDU_API_ENDPOINT")
    channel_id = os.getenv("IAEDU_API_CHANNEL")
    api_key = os.getenv("IAEDU_API_KEY")

    if not all([url, channel_id, api_key]):
        logger.error("IAEdu environment variables are not fully configured.")
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

    import json
    for line in response.iter_lines():
        if line:
            try:
                data = json.loads(line.decode("utf-8"))
                if data.get("type") == "message":
                    content = data["content"]["content"]
                    return content
                elif data.get("type") == "error":
                    logger.error("[IAEDU] API returned error event: %s", data.get("content", "unknown error"))
                    return None
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                logger.debug("[IAEDU] Could not parse line: %s", exc)
                continue

    logger.warning("[IAEDU] No parseable 'message' event found in response stream.")
    return None