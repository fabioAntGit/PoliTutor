
from fastapi import requests

class OpenRouterChat:
    """
    Minimal sync wrapper for OpenRouter chat completions endpoint.
    """

    def __init__(self, model: str, api_key: str, base_url: str = "https://openrouter.ai/api/v1", extra_headers: dict = None):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.extra_headers = extra_headers or {}

    def _headers(self):
        h = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        h.update(self.extra_headers)
        return h

    def chat(self, messages, **kwargs):
        """
        messages: list of dicts {'role': 'user'|'assistant'|'system', 'content': '...'}
        returns parsed JSON response
        """
        payload = {"model": self.model, "messages": messages}
        payload.update(kwargs)
        url = f"{self.base_url}/chat/completions"
        resp = requests.post(url, headers=self._headers(),
                             json=payload, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def __call__(self, messages, **kwargs):
        return self.chat(messages=messages, **kwargs)
