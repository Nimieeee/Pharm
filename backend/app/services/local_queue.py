"""
Local Inference Queue

Serializes requests to local BitNet model.
Prevents VPS overload from concurrent local inference.

Features:
- Semaphore-based concurrency control
- Queue size limits with 503 rejection
- Queue position tracking
"""

import asyncio
from fastapi import HTTPException


class LocalInferenceQueue:
    """
    Queue for local BitNet inference requests.
    
    Features:
    - 1 concurrent request (semaphore)
    - Max 5 queued requests
    - 503 error when queue full
    """
    
    def __init__(self, max_queue_size: int = 5):
        """
        Initialize queue.
        
        Args:
            max_queue_size: Maximum concurrent queued requests
        """
        self._semaphore = asyncio.Semaphore(1)  # 1 concurrent request
        self._queue_size = 0
        self._max_queue = max_queue_size
    
    async def submit(self, request_fn):
        """
        Submit request to queue.
        
        Args:
            request_fn: Async function to execute
            
        Returns:
            Result from request_fn
            
        Raises:
            HTTPException: 503 if queue is full
        """
        if self._queue_size >= self._max_queue:
            raise HTTPException(
                status_code=503,
                detail="Local model queue full, try remote mode"
            )
        
        self._queue_size += 1
        try:
            async with self._semaphore:
                return await request_fn()
        finally:
            self._queue_size -= 1
    
    def is_busy(self) -> bool:
        """
        Check if queue has pending requests.
        
        Returns:
            True if queue is processing or has queued requests
        """
        return self._queue_size > 0
    
    def queue_position(self) -> int:
        """
        Return current queue position.
        
        Returns:
            Number of requests in queue
        """
        return self._queue_size
    
    def available_slots(self) -> int:
        """
        Return available queue slots.
        
        Returns:
            Number of available slots
        """
        return self._max_queue - self._queue_size


# Singleton instance
local_queue = LocalInferenceQueue(max_queue_size=5)
