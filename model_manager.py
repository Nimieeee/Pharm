# model_manager.py
import os
import streamlit as st
import time
from typing import List, Dict, Generator, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum
import logging

# Import existing Groq functionality
from groq_llm import GroqLLM, generate_completion, generate_completion_stream
from error_handler import ErrorHandler, ErrorType, RetryConfig

logger = logging.getLogger(__name__)

class ModelTier(Enum):
    """Model tier enumeration"""
    FAST = "fast"
    PREMIUM = "premium"

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    name: str
    display_name: str
    model_id: str
    tier: ModelTier
    description: str
    max_tokens: int = 1024
    temperature: float = 0.0
    cost_per_token: float = 0.0
    speed_rating: int = 5  # 1-10 scale
    quality_rating: int = 5  # 1-10 scale

class ModelManager:
    """
    Manages multiple Groq models with tier selection, configuration, and comprehensive error handling.
    Handles model selection, configuration, response generation with retry mechanisms.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided")
        
        # Initialize error handling
        self.error_handler = ErrorHandler()
        self.retry_config = RetryConfig(max_attempts=3, base_delay=2.0, max_delay=30.0)
        
        # Initialize Groq LLM client
        self.groq_client = GroqLLM(api_key=self.api_key)
        
        # Initialize model configurations
        self._initialize_model_configs()
        
        # Set default model
        self.current_model_tier = ModelTier.FAST
        
        # Track model health and performance
        self.model_health = {tier: True for tier in ModelTier}
        self.model_failures = {tier: 0 for tier in ModelTier}
        self.last_success = {tier: time.time() for tier in ModelTier}
    
    def _initialize_model_configs(self):
        """Initialize model configurations from environment variables"""
        fast_model = os.environ.get("GROQ_FAST_MODEL", "gemma2-9b-it")
        premium_model = os.environ.get("GROQ_PREMIUM_MODEL", "qwen/qwen3-32b")
        
        self.model_configs = {
            ModelTier.FAST: ModelConfig(
                name="fast",
                display_name="Fast Mode (Gemma2-9B-IT)",
                model_id=fast_model,
                tier=ModelTier.FAST,
                description="Quick responses with good quality for general pharmacology questions",
                max_tokens=1024,
                temperature=0.0,
                cost_per_token=0.00001,  # Example cost
                speed_rating=9,
                quality_rating=7
            ),
            ModelTier.PREMIUM: ModelConfig(
                name="premium",
                display_name="Premium Mode (Qwen3-32B)",
                model_id=premium_model,
                tier=ModelTier.PREMIUM,
                description="High-quality responses with advanced reasoning for complex pharmacology topics",
                max_tokens=2048,
                temperature=0.0,
                cost_per_token=0.00005,  # Example cost
                speed_rating=6,
                quality_rating=9
            )
        }
    
    def get_available_models(self) -> List[ModelConfig]:
        """Get list of available model configurations"""
        return list(self.model_configs.values())
    
    def get_model_config(self, tier: ModelTier) -> ModelConfig:
        """Get configuration for a specific model tier"""
        return self.model_configs.get(tier, self.model_configs[ModelTier.FAST])
    
    def set_current_model(self, tier: ModelTier) -> None:
        """Set the current active model tier"""
        if tier in self.model_configs:
            self.current_model_tier = tier
            logger.info(f"Model tier changed to: {tier.value}")
        else:
            raise ValueError(f"Invalid model tier: {tier}")
    
    def get_current_model(self) -> ModelConfig:
        """Get the current active model configuration"""
        return self.model_configs[self.current_model_tier]
    
    def generate_response(
        self,
        messages: List[Dict],
        tier: Optional[ModelTier] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a complete response using the specified or current model tier with error handling
        
        Args:
            messages: List of message dictionaries
            tier: Model tier to use (defaults to current)
            temperature: Sampling temperature (defaults to model config)
            max_tokens: Maximum tokens to generate (defaults to model config)
            
        Returns:
            Generated response text
        """
        model_tier = tier or self.current_model_tier
        
        # Try primary model first, then fallback if needed
        for attempt_tier in self._get_model_fallback_order(model_tier):
            try:
                response = self._generate_with_retry(
                    messages, attempt_tier, temperature, max_tokens
                )
                
                # Update success tracking
                self.last_success[attempt_tier] = time.time()
                self.model_failures[attempt_tier] = 0
                self.model_health[attempt_tier] = True
                
                if attempt_tier != model_tier:
                    logger.info(f"Successfully used fallback model {attempt_tier.value}")
                
                return response
                
            except Exception as e:
                # Update failure tracking
                self.model_failures[attempt_tier] += 1
                if self.model_failures[attempt_tier] >= 3:
                    self.model_health[attempt_tier] = False
                
                error_info = self.error_handler.handle_error(
                    e, ErrorType.MODEL_API, f"generate_response_{attempt_tier.value}"
                )
                
                logger.warning(f"Model {attempt_tier.value} failed: {str(e)}")
                
                # If this was the last fallback option, raise the error
                if attempt_tier == self._get_model_fallback_order(model_tier)[-1]:
                    self.error_handler.display_error_to_user(error_info)
                    raise e
        
        # This should never be reached
        raise Exception("All model tiers failed")
    
    def _generate_with_retry(
        self,
        messages: List[Dict],
        tier: ModelTier,
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> str:
        """Generate response with retry logic for a specific model tier"""
        config = self.get_model_config(tier)
        
        # Use provided parameters or fall back to model config
        temp = temperature if temperature is not None else config.temperature
        max_tok = max_tokens if max_tokens is not None else config.max_tokens
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                response = self.groq_client.generate_response(
                    messages=messages,
                    model_type=config.name,
                    temperature=temp,
                    max_tokens=max_tok
                )
                
                logger.info(f"Generated response using {config.display_name} (attempt {attempt})")
                return response
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Don't retry for certain types of errors
                if "invalid" in error_str or "bad request" in error_str:
                    logger.error(f"Non-retryable error with {config.display_name}: {str(e)}")
                    raise e
                
                # If this is the last attempt, raise the error
                if attempt == self.retry_config.max_attempts:
                    logger.error(f"All retry attempts failed for {config.display_name}")
                    raise e
                
                # Wait before retry
                delay = self.error_handler.get_retry_delay(attempt, self.retry_config)
                logger.info(f"Retrying {config.display_name} in {delay:.1f} seconds (attempt {attempt}/{self.retry_config.max_attempts})")
                time.sleep(delay)
        
        raise Exception(f"Max retries exceeded for {config.display_name}")
    
    def _get_model_fallback_order(self, primary_tier: ModelTier) -> List[ModelTier]:
        """Get the order of models to try, starting with primary and including fallbacks"""
        fallback_order = [primary_tier]
        
        # Add healthy alternative models as fallbacks
        for tier in ModelTier:
            if tier != primary_tier and self.model_health[tier]:
                fallback_order.append(tier)
        
        # If no healthy alternatives, try all models anyway
        if len(fallback_order) == 1:
            for tier in ModelTier:
                if tier != primary_tier:
                    fallback_order.append(tier)
        
        return fallback_order
    
    def stream_response(
        self,
        messages: List[Dict],
        tier: Optional[ModelTier] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        Stream response chunks using the specified or current model tier with error handling
        
        Args:
            messages: List of message dictionaries
            tier: Model tier to use (defaults to current)
            temperature: Sampling temperature (defaults to model config)
            max_tokens: Maximum tokens to generate (defaults to model config)
            
        Yields:
            Response text chunks
        """
        model_tier = tier or self.current_model_tier
        
        # Try primary model first, then fallback if needed
        for attempt_tier in self._get_model_fallback_order(model_tier):
            try:
                yield from self._stream_with_retry(
                    messages, attempt_tier, temperature, max_tokens
                )
                
                # Update success tracking
                self.last_success[attempt_tier] = time.time()
                self.model_failures[attempt_tier] = 0
                self.model_health[attempt_tier] = True
                
                if attempt_tier != model_tier:
                    logger.info(f"Successfully used fallback model {attempt_tier.value} for streaming")
                
                return  # Successfully streamed, exit
                
            except Exception as e:
                # Update failure tracking
                self.model_failures[attempt_tier] += 1
                if self.model_failures[attempt_tier] >= 3:
                    self.model_health[attempt_tier] = False
                
                error_info = self.error_handler.handle_error(
                    e, ErrorType.MODEL_API, f"stream_response_{attempt_tier.value}"
                )
                
                logger.warning(f"Streaming failed for model {attempt_tier.value}: {str(e)}")
                
                # If this was the last fallback option, try non-streaming fallback
                if attempt_tier == self._get_model_fallback_order(model_tier)[-1]:
                    logger.info("Attempting non-streaming fallback")
                    try:
                        # Fallback to non-streaming response
                        response = self.generate_response(messages, model_tier, temperature, max_tokens)
                        # Simulate streaming by yielding chunks
                        chunk_size = 50
                        for i in range(0, len(response), chunk_size):
                            yield response[i:i+chunk_size]
                            time.sleep(0.05)  # Small delay to simulate streaming
                        return
                    except Exception as fallback_error:
                        logger.error(f"Non-streaming fallback also failed: {str(fallback_error)}")
                        self.error_handler.display_error_to_user(error_info)
                        raise e
    
    def _stream_with_retry(
        self,
        messages: List[Dict],
        tier: ModelTier,
        temperature: Optional[float],
        max_tokens: Optional[int]
    ) -> Generator[str, None, None]:
        """Stream response with retry logic for a specific model tier"""
        config = self.get_model_config(tier)
        
        # Use provided parameters or fall back to model config
        temp = temperature if temperature is not None else config.temperature
        max_tok = max_tokens if max_tokens is not None else config.max_tokens
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                logger.info(f"Starting streaming with {config.display_name} (attempt {attempt})")
                
                yield from self.groq_client.stream_response(
                    messages=messages,
                    model_type=config.name,
                    temperature=temp,
                    max_tokens=max_tok
                )
                
                return  # Successfully streamed, exit
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Don't retry for certain types of errors
                if "invalid" in error_str or "bad request" in error_str:
                    logger.error(f"Non-retryable streaming error with {config.display_name}: {str(e)}")
                    raise e
                
                # If this is the last attempt, raise the error
                if attempt == self.retry_config.max_attempts:
                    logger.error(f"All streaming retry attempts failed for {config.display_name}")
                    raise e
                
                # Wait before retry
                delay = self.error_handler.get_retry_delay(attempt, self.retry_config)
                logger.info(f"Retrying streaming for {config.display_name} in {delay:.1f} seconds")
                time.sleep(delay)
    
    def get_model_info(self, tier: ModelTier) -> Dict[str, any]:
        """Get detailed information about a model tier"""
        config = self.get_model_config(tier)
        return {
            "name": config.display_name,
            "description": config.description,
            "model_id": config.model_id,
            "max_tokens": config.max_tokens,
            "speed_rating": config.speed_rating,
            "quality_rating": config.quality_rating,
            "cost_per_token": config.cost_per_token
        }
    
    def validate_model_availability(self) -> Dict[ModelTier, bool]:
        """
        Validate that all configured models are available
        
        Returns:
            Dictionary mapping model tiers to availability status
        """
        availability = {}
        
        for tier, config in self.model_configs.items():
            try:
                # Test with a simple message
                test_messages = [{"role": "user", "content": "Hello"}]
                self.generate_response(test_messages, tier=tier)
                availability[tier] = True
                logger.info(f"Model {config.display_name} is available")
            except Exception as e:
                availability[tier] = False
                logger.warning(f"Model {config.display_name} is not available: {str(e)}")
        
        return availability

# Session state management for model selection
def get_session_model_tier() -> ModelTier:
    """Get the current model tier from session state"""
    # Check if we have a model preference in session state
    model_pref = st.session_state.get('model_preference', 'fast')
    return ModelTier.PREMIUM if model_pref == 'premium' else ModelTier.FAST

def set_session_model_tier(tier: ModelTier) -> None:
    """Set the model tier in session state and persist to user preferences"""
    model_pref = 'premium' if tier == ModelTier.PREMIUM else 'fast'
    st.session_state.model_preference = model_pref
    
    # Update session manager if available
    if hasattr(st.session_state, 'session_manager') and st.session_state.session_manager:
        st.session_state.session_manager.update_model_preference(model_pref)

# Global model manager instance
_model_manager = None

def get_model_manager() -> ModelManager:
    """Get or create the global model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager