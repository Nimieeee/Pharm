import asyncio
import time
from typing import Optional

class RateLimiter:
    """
    Token Bucket Rate Limiter for AI API calls.
    Ensures we don't hit rate limits by waiting for available slots.
    """
    def __init__(self, calls_per_second: float = 1.0, burst: int = 5):
        self.rate = calls_per_second
        self.capacity = burst
        self.tokens = burst
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def wait_for_slot(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now
            
            # Refill tokens based on elapsed time
            new_tokens = elapsed * self.rate
            if new_tokens > 0:
                self.tokens = min(self.capacity, self.tokens + new_tokens)
            
            # Wait if no tokens available
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
                self.last_update = time.monotonic()
            else:
                self.tokens -= 1

# Default instance for Mistral API (conservative limits)
# Free tier might be lower, adjusting to ~1 request per 2 seconds to be safe
mistral_limiter = RateLimiter(calls_per_second=0.5, burst=2)
