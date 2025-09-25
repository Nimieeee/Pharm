# openrouter_llm.py
import os
import requests
from typing import List, Generator


class OpenRouterChat:
    """
    Minimal OpenRouter wrapper for qwen/qwen3-32b.
    Uses OpenRouter's OpenAI-compatible endpoint: https://openrouter.ai/api/v1
    """

    def __init__(self, model: str = "qwen/qwen3-32b", api_key: str = None, api_base: str = "https://openrouter.ai/api/v1"):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.api_base = api_base
        if not self.api_key:
            raise EnvironmentError("OPENROUTER_API_KEY required to call OpenRouter.")

    def chat(self, messages: List[dict], temperature: float = 0.0, max_tokens: int = 1024) -> str:
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {"model": self.model, "messages": messages, "temperature": temperature, "max_output_tokens": max_tokens}
        resp = requests.post(url, json=body, headers=headers, timeout=120)
        resp.raise_for_status()
        j = resp.json()
        return j["choices"][0]["message"]["content"]

    def stream_chat(self, messages: List[dict], temperature: float = 0.0, max_tokens: int = 1024) -> Generator[str, None, None]:
        """
        Fallback streaming: call chat() then yield chunks. Replace with real streaming parsing if available.
        """
        text = self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        chunk_size = 80
        for i in range(0, len(text), chunk_size):
            yield text[i : i + chunk_size]
