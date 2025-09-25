"""
Comprehensive error handling and fallback system for the Pharmacology Chat App.
Provides centralized error handling, retry mechanisms, and graceful degradation.
"""

import time
import logging
import functools
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import streamlit as st

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Types of errors that can occur in the application"""
    AUTHENTICATION = "authentication"
    DATABASE = "database"
    MODEL_API = "model_api"
    RAG_PIPELINE = "rag_pipeline"
    NETWORK = "network"
    VALIDATION = "validation"
    UNKNOWN = "unknown"

class ErrorSeverity(Enum):
    """Severity levels for errors"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorInfo:
    """Information about an error"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    user_message: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None
    fallback_available: bool = False
    timestamp: Optional[float] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class RetryConfig:
    """Configuration for retry mechanisms"""
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

class ErrorHandler:
    """Centralized error handling and recovery system"""
    
    def __init__(self):
        self.error_counts = {}
        self.last_errors = {}
        self.fallback_modes = {}
    
    def handle_error(
        self,
        error: Exception,
        error_type: ErrorType,
        context: str = "",
        user_friendly: bool = True
    ) -> ErrorInfo:
        """
        Handle an error and return structured error information
        
        Args:
            error: The exception that occurred
            error_type: Type of error
            context: Additional context about where the error occurred
            user_friendly: Whether to show user-friendly messages
            
        Returns:
            ErrorInfo object with error details and recovery options
        """
        error_key = f"{error_type.value}_{context}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = time.time()
        
        # Log the error
        logger.error(f"Error in {context}: {error_type.value} - {str(error)}")
        
        # Generate error info based on type
        if error_type == ErrorType.AUTHENTICATION:
            return self._handle_auth_error(error, context)
        elif error_type == ErrorType.DATABASE:
            return self._handle_database_error(error, context)
        elif error_type == ErrorType.MODEL_API:
            return self._handle_model_api_error(error, context)
        elif error_type == ErrorType.RAG_PIPELINE:
            return self._handle_rag_error(error, context)
        elif error_type == ErrorType.NETWORK:
            return self._handle_network_error(error, context)
        else:
            return self._handle_unknown_error(error, context)
    
    def _handle_auth_error(self, error: Exception, context: str) -> ErrorInfo:
        """Handle authentication-related errors"""
        error_str = str(error).lower()
        
        if "invalid credentials" in error_str or "unauthorized" in error_str:
            return ErrorInfo(
                error_type=ErrorType.AUTHENTICATION,
                severity=ErrorSeverity.MEDIUM,
                message=f"Authentication failed: {str(error)}",
                user_message="Invalid email or password. Please check your credentials and try again.",
                fallback_available=False
            )
        elif "network" in error_str or "connection" in error_str:
            return ErrorInfo(
                error_type=ErrorType.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                message=f"Network error during authentication: {str(error)}",
                user_message="Unable to connect to authentication service. Please check your internet connection and try again.",
                retry_after=5,
                fallback_available=False
            )
        elif "rate limit" in error_str or "too many" in error_str:
            return ErrorInfo(
                error_type=ErrorType.AUTHENTICATION,
                severity=ErrorSeverity.MEDIUM,
                message=f"Rate limit exceeded: {str(error)}",
                user_message="Too many login attempts. Please wait a few minutes before trying again.",
                retry_after=300,  # 5 minutes
                fallback_available=False
            )
        else:
            return ErrorInfo(
                error_type=ErrorType.AUTHENTICATION,
                severity=ErrorSeverity.HIGH,
                message=f"Authentication error: {str(error)}",
                user_message="Authentication service is temporarily unavailable. Please try again later.",
                retry_after=30,
                fallback_available=False
            )
    
    def _handle_database_error(self, error: Exception, context: str) -> ErrorInfo:
        """Handle database-related errors"""
        error_str = str(error).lower()
        
        if "connection" in error_str or "timeout" in error_str:
            return ErrorInfo(
                error_type=ErrorType.DATABASE,
                severity=ErrorSeverity.HIGH,
                message=f"Database connection error: {str(error)}",
                user_message="Database is temporarily unavailable. Your data is safe, please try again in a moment.",
                retry_after=10,
                fallback_available=True
            )
        elif "permission" in error_str or "access" in error_str:
            return ErrorInfo(
                error_type=ErrorType.DATABASE,
                severity=ErrorSeverity.CRITICAL,
                message=f"Database permission error: {str(error)}",
                user_message="Unable to access your data. Please contact support if this persists.",
                fallback_available=False
            )
        else:
            return ErrorInfo(
                error_type=ErrorType.DATABASE,
                severity=ErrorSeverity.HIGH,
                message=f"Database error: {str(error)}",
                user_message="Database operation failed. Please try again.",
                retry_after=5,
                fallback_available=True
            )
    
    def _handle_model_api_error(self, error: Exception, context: str) -> ErrorInfo:
        """Handle AI model API errors"""
        error_str = str(error).lower()
        
        if "rate limit" in error_str or "quota" in error_str:
            return ErrorInfo(
                error_type=ErrorType.MODEL_API,
                severity=ErrorSeverity.MEDIUM,
                message=f"API rate limit exceeded: {str(error)}",
                user_message="AI service is busy. Please wait a moment and try again.",
                retry_after=60,
                fallback_available=True
            )
        elif "timeout" in error_str or "connection" in error_str:
            return ErrorInfo(
                error_type=ErrorType.MODEL_API,
                severity=ErrorSeverity.MEDIUM,
                message=f"API timeout: {str(error)}",
                user_message="AI service is taking longer than usual. Please try again.",
                retry_after=10,
                fallback_available=True
            )
        elif "invalid" in error_str or "bad request" in error_str:
            return ErrorInfo(
                error_type=ErrorType.MODEL_API,
                severity=ErrorSeverity.LOW,
                message=f"Invalid API request: {str(error)}",
                user_message="Unable to process your request. Please try rephrasing your question.",
                fallback_available=True
            )
        else:
            return ErrorInfo(
                error_type=ErrorType.MODEL_API,
                severity=ErrorSeverity.HIGH,
                message=f"Model API error: {str(error)}",
                user_message="AI service is temporarily unavailable. Please try again later.",
                retry_after=30,
                fallback_available=True
            )
    
    def _handle_rag_error(self, error: Exception, context: str) -> ErrorInfo:
        """Handle RAG pipeline errors"""
        return ErrorInfo(
            error_type=ErrorType.RAG_PIPELINE,
            severity=ErrorSeverity.MEDIUM,
            message=f"RAG pipeline error: {str(error)}",
            user_message="Unable to search your documents. I'll answer using my general knowledge instead.",
            fallback_available=True
        )
    
    def _handle_network_error(self, error: Exception, context: str) -> ErrorInfo:
        """Handle network-related errors"""
        return ErrorInfo(
            error_type=ErrorType.NETWORK,
            severity=ErrorSeverity.HIGH,
            message=f"Network error: {str(error)}",
            user_message="Network connection issue. Please check your internet connection and try again.",
            retry_after=10,
            fallback_available=False
        )
    
    def _handle_unknown_error(self, error: Exception, context: str) -> ErrorInfo:
        """Handle unknown errors"""
        return ErrorInfo(
            error_type=ErrorType.UNKNOWN,
            severity=ErrorSeverity.HIGH,
            message=f"Unknown error in {context}: {str(error)}",
            user_message="An unexpected error occurred. Please try again.",
            retry_after=5,
            fallback_available=False
        )
    
    def should_retry(self, error_type: ErrorType, context: str, max_retries: int = 3) -> bool:
        """Check if an operation should be retried"""
        error_key = f"{error_type.value}_{context}"
        count = self.error_counts.get(error_key, 0)
        return count < max_retries
    
    def get_retry_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate retry delay with exponential backoff"""
        delay = config.base_delay * (config.exponential_base ** (attempt - 1))
        delay = min(delay, config.max_delay)
        
        if config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter
        
        return delay
    
    def display_error_to_user(self, error_info: ErrorInfo):
        """Display error message to user in Streamlit"""
        if error_info.severity == ErrorSeverity.CRITICAL:
            st.error(f"🚨 {error_info.user_message}")
        elif error_info.severity == ErrorSeverity.HIGH:
            st.error(f"❌ {error_info.user_message}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            st.warning(f"⚠️ {error_info.user_message}")
        else:
            st.info(f"ℹ️ {error_info.user_message}")
        
        if error_info.retry_after:
            st.info(f"⏱️ Please wait {error_info.retry_after} seconds before trying again.")
        
        if error_info.fallback_available:
            st.info("🔄 Attempting to use alternative method...")

def with_error_handling(
    error_type: ErrorType,
    context: str = "",
    retry_config: Optional[RetryConfig] = None,
    fallback_func: Optional[Callable] = None
):
    """
    Decorator for adding error handling and retry logic to functions
    
    Args:
        error_type: Type of error expected
        context: Context description for logging
        retry_config: Retry configuration
        fallback_func: Fallback function to call on failure
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            error_handler = ErrorHandler()
            config = retry_config or RetryConfig()
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_info = error_handler.handle_error(e, error_type, context)
                    
                    # If this is the last attempt or retries not recommended
                    if attempt == config.max_attempts or not error_info.retry_after:
                        if fallback_func and error_info.fallback_available:
                            logger.info(f"Using fallback for {context}")
                            return fallback_func(*args, **kwargs)
                        else:
                            error_handler.display_error_to_user(error_info)
                            raise e
                    
                    # Wait before retry
                    delay = error_handler.get_retry_delay(attempt, config)
                    logger.info(f"Retrying {context} in {delay:.1f} seconds (attempt {attempt}/{config.max_attempts})")
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise Exception(f"Max retries exceeded for {context}")
        
        return wrapper
    return decorator

# Global error handler instance
_error_handler = ErrorHandler()

def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance"""
    return _error_handler