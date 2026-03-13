"""
Router Service

Intelligent prompt routing based on complexity and privacy.
Determines optimal LLM provider for each request.

Routing Logic:
- fast mode: LOCAL (simple) → GROQ (medium) → POLLINATIONS (complex)
- detailed mode: LOCAL (private) → POLLINATIONS (standard)
- deep_research: Always POLLINATIONS (Sonnet 4.6)
"""

from typing import Optional
from app.core.container import container
from app.services.postprocessing.prompt_processor import prompt_processor


class RouterService:
    """
    Intelligent prompt routing service.
    
    Features:
    - Complexity-based routing
    - Privacy-aware routing (local for sensitive data)
    - Queue status awareness
    - Mode-specific routing strategies
    """
    
    def __init__(self):
        """Initialize RouterService"""
        self._queue = None
    
    @property
    def queue(self):
        """Lazy load local inference queue from container"""
        if self._queue is None:
            try:
                self._queue = container.get('local_queue')
            except KeyError:
                self._queue = None
        return self._queue
    
    def route(self, prompt: str, token_count: int, mode: str) -> str:
        """
        Determine optimal provider based on mode + complexity.
        
        Args:
            prompt: User input text
            token_count: Estimated token count
            mode: Request mode (fast, detailed, deep_research, etc.)
            
        Returns:
            Provider name string (local, groq, pollinations, nvidia)
        """
        complexity = prompt_processor.score_complexity(prompt, token_count)
        is_private = prompt_processor.detect_privacy(prompt)
        queue_busy = self.queue.is_busy() if self.queue else False
        
        if mode == "fast":
            return self._route_fast(complexity, queue_busy)
        elif mode == "detailed":
            return self._route_detailed(complexity, is_private, queue_busy)
        elif mode in ("deep_research", "deep_research_elite", "deep_research_single_pass"):
            return self._route_elite()
        else:
            return self._route_default(complexity, queue_busy)
    
    def _route_fast(self, complexity: float, queue_busy: bool) -> str:
        """
        Route for fast mode.

        Priority: LOCAL → GROQ → POLLINATIONS
        """
        if complexity < 0.3 and not queue_busy:
            result = "local"  # BitNet 2B for simple prompts
            # Fallback: if local isn't available, route to groq
            if not self._is_local_available():
                return "groq"
            return result
        elif complexity < 0.6:
            return "groq"  # Groq 8B for medium complexity
        else:
            return "pollinations"  # Sonnet 4.6 for complex

    def _route_detailed(self, complexity: float, is_private: bool, queue_busy: bool) -> str:
        """
        Route for detailed mode.

        Priority: LOCAL (private) → LOCAL (simple) → POLLINATIONS
        """
        if is_private:
            result = "local"  # Privacy: never leaves VPS
            # Fallback: local isn't deployed, use groq
            if not self._is_local_available():
                return "groq"
            return result

        if complexity < 0.4 and not queue_busy:
            result = "local"  # BitNet 8B for simple prompts
            # Fallback: local isn't available
            if not self._is_local_available():
                return "groq"
            return result

        return "pollinations"  # Sonnet 4.6 for standard

    def _is_local_available(self) -> bool:
        """
        Check if local BitNet server is reachable.

        Returns:
            True if local inference is available
        """
        # For now, local BitNet is not deployed
        # Return False to always fallback to cloud providers
        return False
    
    def _route_elite(self) -> str:
        """
        Route for deep research elite mode.
        
        Always POLLINATIONS (Sonnet 4.6 with 256K context)
        """
        return "pollinations"
    
    def _route_default(self, complexity: float, queue_busy: bool) -> str:
        """
        Default routing for unknown modes.
        
        Priority: GROQ → POLLINATIONS
        """
        if complexity < 0.5 and not queue_busy:
            return "groq"
        return "pollinations"
    
    def should_use_local(self, prompt: str, mode: str) -> bool:
        """
        Quick check if local inference should be used.
        
        Args:
            prompt: User input text
            mode: Request mode
            
        Returns:
            True if local inference is appropriate
        """
        provider = self.route(prompt, prompt_processor.estimate_tokens(prompt), mode)
        return provider == "local"


# Singleton instance
router_service = RouterService()
