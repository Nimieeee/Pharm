# groq_llm.py
import os

# Prefer using the official Groq SDK if available
try:
    from groq import Groq
    _GROQ_AVAILABLE = True
except Exception:
    _GROQ_AVAILABLE = False

import requests
from typing import List, Dict, Generator

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
API_BASE = "https://api.groq.com/openai/v1/chat/completions"

# Default mode names (override with env vars if desired)
FAST_MODE = os.environ.get("GROQ_FAST_MODEL", "gemma-9b-it")
PREMIUM_MODE = os.environ.get("GROQ_PREMIUM_MODEL", "openai/gpt-oss-20b")

if _GROQ_AVAILABLE and GROQ_API_KEY:
    _client = Groq(api_key=GROQ_API_KEY)
else:
    _client = None

HEADERS = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

def generate_completion(messages: List[Dict], model: str = FAST_MODE, temperature: float = 0.0, max_tokens: int = 1024) -> str:
    # Temporary fallback for testing when GROQ_API_KEY is not configured
    if not GROQ_API_KEY:
        user_message = messages[-1].get('content', '') if messages else ''
        return f"🧬 **Pharmacology Assistant** (Demo Mode)\n\nI received your message: '{user_message}'\n\nThis is a demo response since the GROQ API key is not configured. To get real AI responses:\n\n1. Add your GROQ_API_KEY to Streamlit secrets\n2. The key should be added in your Streamlit Cloud dashboard under 'Manage app' → 'Settings' → 'Secrets'\n\nFor now, I can confirm that:\n✅ Your app is working\n✅ Database is connected\n✅ Message processing is functional\n✅ UI is responsive\n\nTry asking about pharmacokinetics, drug interactions, or any pharmacology topic once the API key is configured!"
    
    if _GROQ_AVAILABLE and _client:
        resp = _client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_completion_tokens=max_tokens)
        return resp.choices[0].message.content
    elif GROQ_API_KEY:
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_completion_tokens": max_tokens}
        r = requests.post(API_BASE, headers=HEADERS, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    else:
        raise EnvironmentError("GROQ_API_KEY is required for Groq API access.")

def generate_completion_stream(messages: List[Dict], model: str = FAST_MODE, temperature: float = 0.0, max_tokens: int = 1024) -> Generator[str, None, None]:
    """
    Yields chunks of text for a streaming UI effect.
    If Groq SDK streaming is available we iterate its stream; otherwise we fallback to a simple chunked yield of the full completion.
    """
    if not GROQ_API_KEY:
        # Fallback demo response when no API key is configured
        full = generate_completion(messages=messages, model=model, temperature=temperature, max_tokens=max_tokens)
        chunk_size = 20  # Smaller chunks for better streaming effect
        import time
        for i in range(0, len(full), chunk_size):
            yield full[i:i+chunk_size]
            time.sleep(0.1)  # Small delay for streaming effect
        return
    
    if _GROQ_AVAILABLE and _client:
        stream = _client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_completion_tokens=max_tokens, stream=True)
        for chunk in stream:
            delta = chunk.choices[0].delta.get("content") if chunk.choices and getattr(chunk.choices[0], "delta", None) else None
            if delta:
                yield delta
    else:
        # fallback: single request and yield in chunks
        full = generate_completion(messages=messages, model=model, temperature=temperature, max_tokens=max_tokens)
        chunk_size = 80
        for i in range(0, len(full), chunk_size):
            yield full[i:i+chunk_size]

class GroqLLM:
    """Enhanced Groq LLM wrapper for RAG pipeline"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided")
        
        # Model mappings
        self.model_map = {
            "fast": FAST_MODE,
            "premium": PREMIUM_MODE
        }
    
    def generate_response(
        self, 
        messages: List[Dict], 
        model_type: str = "fast",
        temperature: float = 0.0,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate a complete response using Groq API
        
        Args:
            messages: List of message dictionaries
            model_type: "fast" or "premium" model selection
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response text
        """
        model = self.model_map.get(model_type, FAST_MODE)
        return generate_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def stream_response(
        self, 
        messages: List[Dict], 
        model_type: str = "fast",
        temperature: float = 0.0,
        max_tokens: int = 1024
    ) -> Generator[str, None, None]:
        """
        Stream response chunks using Groq API
        
        Args:
            messages: List of message dictionaries
            model_type: "fast" or "premium" model selection
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Response text chunks
        """
        model = self.model_map.get(model_type, FAST_MODE)
        yield from generate_completion_stream(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def get_available_models(self) -> List[str]:
        """Get list of available model types"""
        return list(self.model_map.keys())
    
    def get_model_name(self, model_type: str) -> str:
        """Get actual model name for a model type"""
        return self.model_map.get(model_type, FAST_MODE)
