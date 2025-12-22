import asyncio
import time

class GlobalRateLimiter:
    """
    Ensures that no matter how many files you upload or chat requests you send,
    the backend never calls Mistral faster than the configured limit.
    Default: 0.8 requests per second (approx 1 request every 1.25 seconds).
    """
    def __init__(self, requests_per_second=0.8):
        self.delay = 1.0 / requests_per_second
        self.last_call_time = 0
        self._lock = asyncio.Lock()

    async def wait_for_slot(self):
        async with self._lock:
            current_time = time.time()
            elapsed = current_time - self.last_call_time
            
            if elapsed < self.delay:
                wait_time = self.delay - elapsed + 0.1  # +0.1s buffer
                await asyncio.sleep(wait_time)
            
            self.last_call_time = time.time()

# Initialize a single global instance
# Set to 0.8 (approx 1 req every 1.25s) to be super safe for Free Tier
mistral_limiter = GlobalRateLimiter(requests_per_second=0.8)
