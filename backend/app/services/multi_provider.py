"""
Multi-Provider AI Service
Intelligently orchestrates Mistral, NVIDIA NIM, and Groq for optimal performance and scale.

Strategy:
- Priority-based routing: Best provider for each mode (Fast→Groq, Detailed→NVIDIA, Research→NVIDIA)
- Health-aware failover: Automatic fallback on 429 rate limits with cooldown periods
- Weighted distribution: NVIDIA (80%), Groq (15%), Mistral (5%) for load balancing
- Supports ~1,000 concurrent users with combined 100+ RPM capacity
"""

import os
import httpx
import asyncio
from typing import Optional, AsyncGenerator, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import time
import random

from app.core.config import settings


class Provider(Enum):
    MISTRAL = "mistral"
    GROQ = "groq"
    NVIDIA = "nvidia"
    POLLINATIONS = "pollinations"


@dataclass
class ProviderConfig:
    name: Provider
    api_key: str
    base_url: str
    models: Dict[str, str]  # mode -> model_name
    headers: Dict[str, str]
    weight: float = 1.0  # Traffic distribution weight
    rpm_limit: int = 100  # Requests per minute limit
    last_used: float = 0
    error_count: int = 0
    exhausted_until: float = 0  # Timestamp when rate limit expires
    request_count: int = 0  # Requests in current minute
    minute_start: float = field(default_factory=time.time)
    

class MultiProviderService:
    """
    Load-balanced AI provider with intelligent routing and health-aware failover.
    
    Architecture:
    - Priority routing: Each mode has a preferred provider order
    - Weight-based distribution: NVIDIA (80%), Groq (15%), Mistral (5%)
    - Rate limit tracking: Marks providers as exhausted on 429 errors
    - Automatic cooldown: 60s for RPM limits, 24h for daily limits
    """
    
    # Mode-to-provider priority mapping
    MODE_PRIORITIES = {
        "fast": [Provider.GROQ, Provider.MISTRAL, Provider.NVIDIA],
        "detailed": [Provider.MISTRAL, Provider.NVIDIA, Provider.GROQ],
        "deep_research": [Provider.NVIDIA, Provider.MISTRAL, Provider.GROQ],
        "deep_research_elite": [Provider.POLLINATIONS], # Force Pollinations for Elite massive context
        "deep_research_single_pass": [Provider.GROQ], # Force Groq for high TPM and Kimi-K2-Instruct
    }
    
    def __init__(self):
        self.providers: Dict[Provider, ProviderConfig] = {}
        self._lock = asyncio.Lock()
        
        # Initialize NVIDIA NIM (Primary for detailed/research)
        nvidia_key = settings.NVIDIA_API_KEY or os.getenv("NVIDIA_API_KEY", "")
        if nvidia_key:
            self.providers[Provider.NVIDIA] = ProviderConfig(
                name=Provider.NVIDIA,
                api_key=nvidia_key,
                base_url="https://integrate.api.nvidia.com/v1",
                models={
                    "fast": "nvidia/llama-3.1-nemotron-70b-instruct",
                    "detailed": "openai/gpt-oss-120b",
                    "deep_research": "meta/llama-3.3-70b-instruct",
                },
                headers={
                    "Authorization": f"Bearer {nvidia_key}",
                    "Content-Type": "application/json",
                },
                weight=0.80,  # 80% of traffic
                rpm_limit=40,
            )
            print("✅ NVIDIA NIM provider initialized (Primary - 80% weight)")
        
        # Initialize Groq (Primary for fast mode)
        groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        if groq_key:
            self.providers[Provider.GROQ] = ProviderConfig(
                name=Provider.GROQ,
                api_key=groq_key,
                base_url="https://api.groq.com/openai/v1",
                models={
                    "fast": "llama-3.1-8b-instant",
                    "detailed": "llama-3.3-70b-versatile",
                    "deep_research": "deepseek-r1-distill-qwen-32b",
                    "deep_research_single_pass": "moonshotai/kimi-k2-instruct",
                },
                headers={
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json",
                },
                weight=0.15,  # 15% of traffic
                rpm_limit=30,
            )
            print("✅ Groq provider initialized (Fast mode - 15% weight)")
            
        # Initialize Pollinations (Primary for elite deep research)
        pollinations_key = os.getenv("POLLINATIONS_API_KEY", "")
        if pollinations_key:
            self.providers[Provider.POLLINATIONS] = ProviderConfig(
                name=Provider.POLLINATIONS,
                api_key=pollinations_key,
                base_url="https://gen.pollinations.ai/v1",
                models={
                    "fast": "gemini-fast",
                    "detailed": "claude-airforce",
                    "deep_research": "claude-airforce",
                    "deep_research_elite": "claude-airforce", # Massive context window
                    "deep_research_single_pass": "gemini-fast",
                },
                headers={
                    "Authorization": f"Bearer {pollinations_key}",
                    "Content-Type": "application/json",
                },
                weight=1.0,
                rpm_limit=10,
            )
            print("✅ Pollinations provider initialized (Elite mode)")
        
        # Initialize Mistral (Fallback/safety net)
        if settings.MISTRAL_API_KEY:
            self.providers[Provider.MISTRAL] = ProviderConfig(
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
                },
                weight=0.05,  # 5% of traffic (safety net)
                rpm_limit=30,  # Increased budget for active research
            )
            print("✅ Mistral provider initialized (Fallback - 5% weight)")
        
        if not self.providers:
            raise ValueError("No AI providers configured! Set NVIDIA_API_KEY, GROQ_API_KEY, or MISTRAL_API_KEY")
        
        # Calculate combined capacity
        total_rpm = sum(p.rpm_limit for p in self.providers.values())
        total_rph = total_rpm * 60
        total_rpd = total_rph * 24
        
        # Log initialized providers and capacity
        provider_names = [p.name.value for p in self.providers.values()]
        print(f"🔄 Multi-provider routing enabled: {provider_names}")
        print(f"📊 Combined capacity: {total_rpm} RPM, {total_rph} RPH, {total_rpd} RPD")
    
    def _is_provider_healthy(self, provider: ProviderConfig) -> bool:
        """Check if provider is healthy and not rate-limited"""
        now = time.time()
        
        # Check if exhausted (rate limited)
        if provider.exhausted_until > now:
            return False
        
        # Check if too many recent errors
        if provider.error_count >= 3:
            if now - provider.last_used > 60:
                provider.error_count = 0  # Reset after cooldown
            else:
                return False
        
        # Check RPM limit
        if now - provider.minute_start > 60:
            # Reset minute counter
            provider.request_count = 0
            provider.minute_start = now
        
        if provider.request_count >= provider.rpm_limit:
            return False
        
        return True
    
    async def get_provider_for_mode(self, mode: str, exclude_providers: set = None) -> Optional[ProviderConfig]:
        """
        Get best available provider for the given mode using priority + health.

        Args:
            mode: The mode (fast, detailed, etc.)
            exclude_providers: Set of provider names to skip (for fallback logic)
        """
        async with self._lock:
            # Get priority order for this mode
            priorities = self.MODE_PRIORITIES.get(mode, self.MODE_PRIORITIES["detailed"])

            # Try providers in priority order
            for provider_enum in priorities:
                if provider_enum not in self.providers:
                    continue

                # Skip excluded providers (for fallback logic)
                if exclude_providers and provider_enum.name in exclude_providers:
                    print(f"⊘ Skipping {provider_enum.name} (excluded for this request)")
                    continue

                provider = self.providers[provider_enum]
                if self._is_provider_healthy(provider):
                    provider.last_used = time.time()
                    provider.request_count += 1
                    model = provider.models.get(mode, provider.models["detailed"])
                    print(f"✅ Selected {provider.name.value} with model {model}")
                    return provider

            # No healthy provider found, use weighted random selection as last resort
            healthy_providers = [
                p for p in self.providers.values()
                if p.exhausted_until < time.time()  # At least not rate-limited
            ]

            if healthy_providers:
                # Weighted random selection
                weights = [p.weight for p in healthy_providers]
                provider = random.choices(healthy_providers, weights=weights, k=1)[0]
                provider.last_used = time.time()
                provider.request_count += 1
                model = provider.models.get(mode, provider.models["detailed"])
                print(f"✅ Selected {provider.name.value} with model {model} (weighted fallback)")
                return provider

            # Absolute last resort: return any provider
            return list(self.providers.values())[0] if self.providers else None
    
    def mark_rate_limited(self, provider: ProviderConfig, is_daily_limit: bool = False):
        """Mark provider as rate-limited with appropriate cooldown"""
        cooldown = 86400 if is_daily_limit else 60  # 24h for daily, 60s for RPM
        provider.exhausted_until = time.time() + cooldown
        limit_type = "daily" if is_daily_limit else "RPM"
        print(f"⚠️ {provider.name.value} {limit_type} limit reached, cooldown: {cooldown}s")
    
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
        json_mode: bool = False,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        exclude_providers: set = None,  # Providers to skip for this request
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response with automatic provider rotation and fallback.

        Args:
            exclude_providers: Set of provider names to skip (e.g., {"groq"} if payload too large)
        """
        last_error = None
        attempted_providers = set(exclude_providers) if exclude_providers else set()

        for attempt in range(len(self.providers)):
            provider = await self.get_provider_for_mode(mode, exclude_providers=attempted_providers)
            if not provider:
                raise Exception("No available providers for this request")

            # Track this provider as attempted
            attempted_providers.add(provider.name.name)

            model = provider.models.get(mode, provider.models["detailed"])

            # Use significantly longer timeout for detailed/research modes (larger context/output)
            timeout = 300.0 if mode in ["detailed", "research", "deep_research"] else 60.0

            print(f"🔄 Attempt {attempt + 1}: {provider.name.value} with model {model} (timeout: {timeout}s)")

            try:
                # Build payload
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                }
                
                # Add penalties if specified (only if non-zero to avoid breaking some providers)
                if frequency_penalty != 0.0:
                    payload["frequency_penalty"] = frequency_penalty
                if presence_penalty != 0.0:
                    payload["presence_penalty"] = presence_penalty
                
                # Apply provider-specific flags 
                # (Removed non-standard chat_template_kwargs to avoid 400 errors)
                    
                if json_mode:
                    if provider.name == Provider.MISTRAL:
                        payload["response_format"] = {"type": "json_object"}
                    elif provider.name in [Provider.GROQ, Provider.NVIDIA]:
                        payload["response_format"] = {"type": "json_object"}
                    
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream(
                        "POST",
                        f"{provider.base_url}/chat/completions",
                        headers=provider.headers,
                        json=payload,
                    ) as response:
                        if response.status_code == 429:
                            # Rate limited, try next provider
                            self.mark_rate_limited(provider, is_daily_limit=False)
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
                                except Exception:
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
        json_mode: bool = False,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        exclude_providers: set = None,  # Providers to skip for this request
    ) -> str:
        """
        Non-streaming generation with fallback.

        Args:
            exclude_providers: Set of provider names to skip (e.g., {"groq"} if payload too large)
        """
        last_error = None
        attempted_providers = set(exclude_providers) if exclude_providers else set()

        for attempt in range(len(self.providers)):
            provider = await self.get_provider_for_mode(mode, exclude_providers=attempted_providers)
            if not provider:
                raise Exception("No available providers for this request")

            # Track this provider as attempted
            attempted_providers.add(provider.name.name)

            model = provider.models.get(mode, provider.models["detailed"])

            try:
                # Build payload
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
                
                # Add penalties if specified
                if frequency_penalty != 0.0:
                    payload["frequency_penalty"] = frequency_penalty
                if presence_penalty != 0.0:
                    payload["presence_penalty"] = presence_penalty
                
                # Apply provider-specific flags 
                # (Removed non-standard chat_template_kwargs to avoid 400 errors)
                    
                if json_mode:
                    if provider.name == Provider.MISTRAL:
                        payload["response_format"] = {"type": "json_object"}
                    elif provider.name in [Provider.GROQ, Provider.NVIDIA]:
                        payload["response_format"] = {"type": "json_object"}

                # Use longer timeout for detailed/research modes (larger context/output)
                timeout = 600.0 if mode in ["detailed", "research", "deep_research", "deep_research_single_pass", "deep_research_elite"] else 60.0
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        f"{provider.base_url}/chat/completions",
                        headers=provider.headers,
                        json=payload,
                    )
                    
                    if response.status_code == 429:
                        self.mark_rate_limited(provider, is_daily_limit=False)
                        continue
                    
                    if response.status_code != 200:
                        self.mark_error(provider)
                        error_text = response.text
                        last_error = f"{provider.name.value}: {response.status_code} - {error_text}"
                        print(f"❌ HTTP {response.status_code} error from {provider.name.value}: {error_text}")
                        continue
                    
                    self.mark_success(provider)
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                    
            except Exception as e:
                self.mark_error(provider)
                last_error = f"{provider.name.value}: {str(e)}"
                print(f"❌ {provider.name.value} generation failed: {e}")
                continue
        
        raise Exception(f"All AI providers failed. Last error: {last_error}")


# Global instance
multi_provider = None

def get_multi_provider() -> MultiProviderService:
    global multi_provider
    if multi_provider is None:
        multi_provider = MultiProviderService()
    return multi_provider
