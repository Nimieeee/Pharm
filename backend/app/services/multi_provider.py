"""
Multi-Provider AI Service
Rotates between Mistral and Groq for load balancing and fallback
"""

import os
import httpx
import asyncio
from typing import Optional, AsyncGenerator, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import time

from app.core.config import settings


class Provider(Enum):
    MISTRAL = "mistral"
    GROQ = "groq"


@dataclass
class ProviderConfig:
    name: Provider
    api_key: str
    base_url: str
    models: Dict[str, str]  # mode -> model_name
    headers: Dict[str, str]
    last_used: float = 0
    error_count: int = 0
    

class MultiProviderService:
    """
    Load-balanced AI provider with automatic rotation and fallback.
    
    Strategy:
    - Round-robin between providers for even distribution
    - Automatic fallback on rate limit or error
    - Track error counts and temporarily disable failing providers
    """
    
    def __init__(self):
        self.providers: List[ProviderConfig] = []
        self.current_index = 0
        self._lock = asyncio.Lock()
        
        # Initialize Mistral
        if settings.MISTRAL_API_KEY:
            self.providers.append(ProviderConfig(
                name=Provider.MISTRAL,
                api_key=settings.MISTRAL_API_KEY,
                base_url="https://api.mistral.ai/v1",
                models={
                    "fast": "mistral-small-latest",
                    "detailed": "mistral-large-latest",
                    "deep_research": "mistral-large-latest",
                },
                headers={
                    "Authorization": f"Bearer {settings.MISTRAL_API_KEY}",
                    "Content-Type": "application/json",
                }
            ))
            print("✅ Mistral provider initialized")
        
        # Initialize Groq
        groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        if groq_key:
            self.providers.append(ProviderConfig(
                name=Provider.GROQ,
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
                models={
                    "fast": "llama-3.1-8b-instant",
                    "detailed": "llama-3.3-70b-versatile",
                    "deep_research": "llama-3.3-70b-versatile",
                },
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                }
            ))
            print("✅ Groq provider initialized")
        
        if not self.providers:
            raise ValueError("No AI providers configured! Set MISTRAL_API_KEY or GROQ_API_KEY")
        
        print(f"🔄 Multi-provider rotation enabled: {[p.name.value for p in self.providers]}")
    
    async def get_next_provider(self) -> ProviderConfig:
        """Get next provider using round-robin with error awareness"""
        async with self._lock:
            # Try to find a healthy provider
            attempts = 0
            while attempts < len(self.providers):
                provider = self.providers[self.current_index]
                self.current_index = (self.current_index + 1) % len(self.providers)
                
                # Skip if too many recent errors (but reset after 60s)
                if provider.error_count >= 3:
                    if time.time() - provider.last_used > 60:
                        provider.error_count = 0  # Reset after cooldown
                    else:
                        attempts += 1
                        continue
                
                provider.last_used = time.time()
                return provider
            
            # If all providers have errors, use the first one anyway
            return self.providers[0]
    
    def mark_error(self, provider: ProviderConfig):
        """Mark a provider as having an error"""
        provider.error_count += 1
        print(f"⚠️ {provider.name.value} error #{provider.error_count}")
    
    def mark_success(self, provider: ProviderConfig):
        """Mark a provider as successful, reset error count"""
        provider.error_count = 0
    
    async def generate_streaming(
        self,
        messages: List[Dict[str, str]],
        mode: str = "detailed",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response with automatic provider rotation and fallback.
        """
        last_error = None
        
        for attempt in range(len(self.providers)):
            provider = await self.get_next_provider()
            model = provider.models.get(mode, provider.models["detailed"])
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    async with client.stream(
                        "POST",
                        f"{provider.base_url}/chat/completions",
                        headers=provider.headers,
                        json={
                            "model": model,
                            "messages": messages,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                            "stream": True,
                        },
                    ) as response:
                        if response.status_code == 429:
                            # Rate limited, try next provider
                            self.mark_error(provider)
                            print(f"🔄 Rate limited on {provider.name.value}, trying next provider...")
                            continue
                        
                        if response.status_code != 200:
                            error_text = await response.aread()
                            self.mark_error(provider)
                            last_error = f"{provider.name.value}: {response.status_code} - {error_text[:200]}"
                            continue
                        
                        # Success! Stream the response
                        self.mark_success(provider)
                        print(f"✅ Using {provider.name.value} ({model})")
                        
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data = line[6:]
                                if data == "[DONE]":
                                    break
                                try:
                                    import json
                                    chunk = json.loads(data)
                                    content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                    if content:
                                        yield content
                                except:
                                    pass
                        return  # Success, exit
                        
            except Exception as e:
                self.mark_error(provider)
                last_error = f"{provider.name.value}: {str(e)}"
                print(f"❌ {provider.name.value} failed: {e}")
                continue
        
        # All providers failed
        raise Exception(f"All AI providers failed. Last error: {last_error}")
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        mode: str = "detailed",
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Non-streaming generation with fallback"""
        last_error = None
        
        for attempt in range(len(self.providers)):
            provider = await self.get_next_provider()
            model = provider.models.get(mode, provider.models["detailed"])
            
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{provider.base_url}/chat/completions",
                        headers=provider.headers,
                        json={
                            "model": model,
                            "messages": messages,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                        },
                    )
                    
                    if response.status_code == 429:
                        self.mark_error(provider)
                        continue
                    
                    if response.status_code != 200:
                        self.mark_error(provider)
                        last_error = f"{provider.name.value}: {response.status_code}"
                        continue
                    
                    self.mark_success(provider)
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                    
            except Exception as e:
                self.mark_error(provider)
                last_error = str(e)
                continue
        
        raise Exception(f"All AI providers failed. Last error: {last_error}")


# Global instance
multi_provider = None

def get_multi_provider() -> MultiProviderService:
    global multi_provider
    if multi_provider is None:
        multi_provider = MultiProviderService()
    return multi_provider
