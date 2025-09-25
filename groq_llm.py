# groq_llm.py
"""
Wrapper for Groq OpenAI-compatible chat completions API.
Supports multiple models (fast + premium).
"""

import os
from openai import OpenAI
from typing import List, Dict, Generator

# Load Groq API key
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("Missing GROQ_API_KEY environment variable.")

# ✅ Groq’s API is OpenAI-compatible
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# Default models (update if Groq renames them)
FAST_MODEL = os.environ.get("GROQ_FAST_MODEL", "gemma-9b-it")
PREMIUM_MODEL = os.environ.get("GROQ_PREMIUM_MODEL", "qwen/qwen-32b")

def generate_completion(
    messages: List[Dict[str, str]],
    model: str = FAST_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> str:
    """
    Single-response generation (no streaming).
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"]

def stream_completion(
    messages: List[Dict[str, str]],
    model: str = FAST_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> Generator[str, None, None]:
    """
    Stream response chunks as they arrive.
    """
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.get("content", "")
        if delta:
            yield delta
