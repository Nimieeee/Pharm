"""
Enhanced Logging Configuration for RAG System
Provides structured logging for all RAG operations with performance metrics
"""

import logging
import logging.config
import time
import json
from typing import Dict, Any, Optional
from functools import wraps
from contextlib import contextmanager

from app.core.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record):
        # Create structured log entry
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'conversation_id'):
            log_entry['conversation_id'] = record.conversation_id
        if hasattr(record, 'operation'):
            log_entry['operation'] = record.operation
        if hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration
        if hasattr(record, 'embedding_model'):
            log_entry['embedding_model'] = record.embedding_model
        if hasattr(record, 'chunk_count'):
            log_entry['chunk_count'] = record.chunk_count
        if hasattr(record, 'file_size'):
            log_entry['file_size'] = record.file_size
        if hasattr(record, 'similarity_score'):
            log_entry['similarity_score'] = record.similarity_score
        if hasattr(record, 'api_response_time'):
            log_entry['api_response_time_ms'] = record.api_response_time
        if hasattr(record, 'cache_hit'):
            log_entry['cache_hit'] = record.cache_hit
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class RAGLogger:
    """Enhanced logger for RAG operations with performance tracking"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.performance_stats = {
            "document_processing": [],
            "embedding_generation": [],
            "similarity_search": [],
            "api_calls": []
        }
    
    def log_document_processing(
        self,
        operation: str,
        filename: str,
        user_id: str,
        conversation_id: str,
        duration: float,
        chunk_count: int = 0,
        file_size: int = 0,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log document processing operations"""
        extra = {
            'operation': operation,
            'user_id': user_id,
            'conversation_id': conversation_id,
            'duration': duration * 1000,  # Convert to milliseconds
            'chunk_count': chunk_count,
            'file_size': file_size
        }
        
        if success:
            self.logger.info(
                f"Document processing completed: {filename} -> {chunk_count} chunks ({duration:.2f}s)",
                extra=extra
            )
        else:
            extra['error_type'] = 'document_processing'
            self.logger.error(
                f"Document processing failed: {filename} - {error}",
                extra=extra
            )
        
        # Track performance stats
        self.performance_stats["document_processing"].append({
            "timestamp": time.time(),
            "duration": duration,
            "chunk_count": chunk_count,
            "file_size": file_size,
            "success": success
        })
    
    def log_embedding_generation(
        self,
        text_length: int,
        user_id: str,
        duration: float,
        embedding_model: str,
        cache_hit: bool = False,
        api_response_time: Optional[float] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log embedding generation operations"""
        extra = {
            'operation': 'embedding_generation',
            'user_id': user_id,
            'duration': duration * 1000,
            'embedding_model': embedding_model,
            'cache_hit': cache_hit
        }
        
        if api_response_time:
            extra['api_response_time'] = api_response_time * 1000
        
        if success:
            cache_status = "cache hit" if cache_hit else "API call"
            self.logger.info(
                f"Embedding generated: {text_length} chars via {cache_status} ({duration:.3f}s)",
                extra=extra
            )
        else:
            extra['error_type'] = 'embedding_generation'
            self.logger.error(
                f"Embedding generation failed: {text_length} chars - {error}",
                extra=extra
            )
        
        # Track performance stats
        self.performance_stats["embedding_generation"].append({
            "timestamp": time.time(),
            "duration": duration,
            "text_length": text_length,
            "cache_hit": cache_hit,
            "api_response_time": api_response_time,
            "success": success
        })
    
    def log_similarity_search(
        self,
        query_length: int,
        user_id: str,
        conversation_id: str,
        duration: float,
        result_count: int,
        max_similarity: float = 0.0,
        avg_similarity: float = 0.0,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Log similarity search operations"""
        extra = {
            'operation': 'similarity_search',
            'user_id': user_id,
            'conversation_id': conversation_id,
            'duration': duration * 1000,
            'chunk_count': result_count,
            'similarity_score': max_similarity
        }
        
        if success:
            self.logger.info(
                f"Similarity search completed: {query_length} chars -> {result_count} results "
                f"(max_sim: {max_similarity:.3f}, avg_sim: {avg_similarity:.3f}, {duration:.3f}s)",
                extra=extra
            )
        else:
            extra['error_type'] = 'similarity_search'
            self.logger.error(
                f"Similarity search failed: {query_length} chars - {error}",
                extra=extra
            )
        
        # Track performance stats
        self.performance_stats["similarity_search"].append({
            "timestamp": time.time(),
            "duration": duration,
            "query_length": query_length,
            "result_count": result_count,
            "max_similarity": max_similarity,
            "avg_similarity": avg_similarity,
            "success": success
        })
    
    def log_api_call(
        self,
        api_name: str,
        operation: str,
        duration: float,
        user_id: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        **kwargs
    ):
        """Log external API calls"""
        extra = {
            'operation': f'api_call_{api_name}',
            'api_response_time': duration * 1000
        }
        
        if user_id:
            extra['user_id'] = user_id
        
        # Add any additional kwargs
        for key, value in kwargs.items():
            if key not in extra:
                extra[key] = value
        
        if success:
            self.logger.info(
                f"API call completed: {api_name}.{operation} ({duration:.3f}s)",
                extra=extra
            )
        else:
            extra['error_type'] = f'api_call_{api_name}'
            self.logger.error(
                f"API call failed: {api_name}.{operation} - {error}",
                extra=extra
            )
        
        # Track performance stats
        self.performance_stats["api_calls"].append({
            "timestamp": time.time(),
            "api_name": api_name,
            "operation": operation,
            "duration": duration,
            "success": success
        })
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {}
        
        for category, data in self.performance_stats.items():
            if not data:
                stats[category] = {
                    "count": 0,
                    "avg_duration": 0,
                    "success_rate": 0
                }
                continue
            
            durations = [item["duration"] for item in data]
            successes = [item["success"] for item in data]
            
            stats[category] = {
                "count": len(data),
                "avg_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "success_rate": sum(successes) / len(successes),
                "recent_operations": data[-10:]  # Last 10 operations
            }
        
        return stats
    
    def clear_performance_stats(self):
        """Clear performance statistics"""
        for category in self.performance_stats:
            self.performance_stats[category] = []
        self.logger.info("Performance statistics cleared")


def performance_monitor(operation_type: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = RAGLogger(func.__module__)
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log successful operation
                logger.logger.info(
                    f"Operation completed: {operation_type} ({duration:.3f}s)",
                    extra={
                        'operation': operation_type,
                        'duration': duration * 1000,
                        'function': func.__name__
                    }
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log failed operation
                logger.logger.error(
                    f"Operation failed: {operation_type} - {str(e)} ({duration:.3f}s)",
                    extra={
                        'operation': operation_type,
                        'duration': duration * 1000,
                        'function': func.__name__,
                        'error_type': operation_type,
                    },
                    exc_info=True
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            logger = RAGLogger(func.__module__)
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log successful operation
                logger.logger.info(
                    f"Operation completed: {operation_type} ({duration:.3f}s)",
                    extra={
                        'operation': operation_type,
                        'duration': duration * 1000,
                        'function': func.__name__
                    }
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log failed operation
                logger.logger.error(
                    f"Operation failed: {operation_type} - {str(e)} ({duration:.3f}s)",
                    extra={
                        'operation': operation_type,
                        'duration': duration * 1000,
                        'function': func.__name__,
                        'error_type': operation_type,
                    },
                    exc_info=True
                )
                
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@contextmanager
def operation_context(operation_name: str, logger: RAGLogger, **context_data):
    """Context manager for tracking operations"""
    start_time = time.time()
    
    try:
        logger.logger.info(
            f"Starting operation: {operation_name}",
            extra={'operation': operation_name, **context_data}
        )
        
        yield
        
        duration = time.time() - start_time
        logger.logger.info(
            f"Operation completed: {operation_name} ({duration:.3f}s)",
            extra={
                'operation': operation_name,
                'duration': duration * 1000,
                **context_data
            }
        )
        
    except Exception as e:
        duration = time.time() - start_time
        logger.logger.error(
            f"Operation failed: {operation_name} - {str(e)} ({duration:.3f}s)",
            extra={
                'operation': operation_name,
                'duration': duration * 1000,
                'error_type': operation_name,
                **context_data
            },
            exc_info=True
        )
        raise


# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'structured': {
            '()': StructuredFormatter,
        },
        'simple': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured' if not settings.DEBUG else 'simple',
            'level': 'DEBUG' if settings.DEBUG else 'INFO'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/rag_system.log',
            'formatter': 'structured',
            'level': 'INFO'
        }
    },
    'loggers': {
        'app.services.embeddings': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if settings.DEBUG else 'INFO',
            'propagate': False
        },
        'app.services.enhanced_rag': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if settings.DEBUG else 'INFO',
            'propagate': False
        },
        'app.services.document_loaders': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if settings.DEBUG else 'INFO',
            'propagate': False
        },
        'app.services.text_splitter': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if settings.DEBUG else 'INFO',
            'propagate': False
        },
        'app.services.migration': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if settings.DEBUG else 'INFO',
            'propagate': False
        }
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO'
    }
}


def setup_logging():
    """Setup logging configuration"""
    import os
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Apply logging configuration
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Create main RAG logger
    rag_logger = RAGLogger('rag_system')
    rag_logger.logger.info("✅ Enhanced RAG logging system initialized")
    
    return rag_logger


# Global logger instance
rag_logger = setup_logging()