# groq_llm.py
import os
import requests
from typing import List, Generator


class GroqChat:
    """
    Groq wrapper for chat completions.
    model: Groq model name (e.g., 'gemma2-9b-it' or larger gemma models).
    """

    def __init__(self, model: str = "gemma2-9b-it", api_key: str = None, api_base: str = "https://api.groq.com/openai/v1"):
        self.model = model
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.api_base = api_base
        if not self.api_key:
            raise EnvironmentError("GROQ_API_KEY environment variable is required to call Groq API.")

    def chat(self, messages: List[dict], temperature: float = 0.0, max_tokens: int = 512) -> str:
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {"model": self.model, "messages": messages, "temperature": temperature, "max_output_tokens": max_tokens}
        resp = requests.post(url, json=body, headers=headers, timeout=120)
        resp.raise_for_status()
        j = resp.json()
        return j["choices"][0]["message"]["content"]

    def stream_chat(self, messages: List[dict], temperature: float = 0.0, max_tokens: int = 512) -> Generator[str, None, None]:
        """
        If Groq provides SSE/chunked streaming, replace this with a streaming parser.
        Fallback: call chat() and yield text chunks for a streaming UI effect.
        """
        text = self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        chunk_size = 80
        for i in range(0, len(text), chunk_size):
            yield text[i : i + chunk_size]
