"""
Performance Optimizer for Pharmacology Chat Application
Implements caching, pagination, and performance monitoring
"""

import time
import functools
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import streamlit as st
import hashlib
import json

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with expiration"""
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    cache_hit: bool = False
    error: Optional[str] = None

class MemoryCache:
    """In-memory cache with TTL and size limits"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self._access_order: List[str] = []
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if datetime.now() > entry.expires_at:
            self.delete(key)
            return None
        
        # Update access stats
        entry.access_count += 1
        entry.last_accessed = datetime.now()
        
        # Move to end of access order (most recently used)
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        return entry.data
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # Remove old entry if exists
        if key in self.cache:
            self.delete(key)
        
        # Check size limit and evict if necessary
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # Add new entry
        self.cache[key] = CacheEntry(
            data=value,
            created_at=datetime.now(),
            expires_at=expires_at
        )
        self._access_order.append(key)
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache"""
        if key in self.cache:
            del self.cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self._access_order.clear()
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if self._access_order:
            lru_key = self._access_order[0]
            self.delete(lru_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        expired_count = sum(1 for entry in self.cache.values() if now > entry.expires_at)
        
        return {
            "total_entries": len(self.cache),
            "expired_entries": expired_count,
            "max_size": self.max_size,
            "hit_rate": self._calculate_hit_rate(),
            "memory_usage_mb": self._estimate_memory_usage()
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_accesses = sum(entry.access_count for entry in self.cache.values())
        if total_accesses == 0:
            return 0.0
        return len(self.cache) / total_accesses
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        # Rough estimation
        return len(self.cache) * 0.001  # Assume 1KB per entry on average

class PerformanceOptimizer:
    """Main performance optimization class"""
    
    def __init__(self):
        """Initialize performance optimizer"""
        self.cache = MemoryCache(max_size=500, default_ttl=300)  # 5 minutes default TTL
        self.metrics: List[PerformanceMetrics] = []
        self.max_metrics = 1000  # Keep last 1000 operations
        
        # Initialize session state cache if not exists
        if 'perf_cache' not in st.session_state:
            st.session_state.perf_cache = {}
    
    def cached_operation(self, cache_key: str, ttl: int = 300):
        """Decorator for caching operation results"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Try cache first
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached_result
                
                # Execute operation
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    
                    # Cache result
                    self.cache.set(cache_key, result, ttl)
                    
                    # Record metrics
                    self._record_metric(
                        operation_name=func.__name__,
                        start_time=start_time,
                        cache_hit=False
                    )
                    
                    logger.debug(f"Cached result for {cache_key}")
                    return result
                    
                except Exception as e:
                    self._record_metric(
                        operation_name=func.__name__,
                        start_time=start_time,
                        cache_hit=False,
                        error=str(e)
                    )
                    raise
            
            return wrapper
        return decorator
    
    def timed_operation(self, operation_name: str):
        """Decorator for timing operations"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    self._record_metric(operation_name, start_time)
                    return result
                except Exception as e:
                    self._record_metric(operation_name, start_time, error=str(e))
                    raise
            return wrapper
        return decorator
    
    def get_cached_user_data(self, user_id: str, data_type: str) -> Optional[Any]:
        """Get cached user data"""
        cache_key = f"user_data:{user_id}:{data_type}"
        return self.cache.get(cache_key)
    
    def set_cached_user_data(self, user_id: str, data_type: str, data: Any, ttl: int = 300) -> None:
        """Set cached user data"""
        cache_key = f"user_data:{user_id}:{data_type}"
        self.cache.set(cache_key, data, ttl)
    
    def invalidate_user_cache(self, user_id: str) -> None:
        """Invalidate all cached data for a user"""
        keys_to_delete = [key for key in self.cache.cache.keys() if key.startswith(f"user_data:{user_id}:")]
        for key in keys_to_delete:
            self.cache.delete(key)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.metrics:
            return {"total_operations": 0}
        
        recent_metrics = [m for m in self.metrics if m.end_time and m.duration]
        
        if not recent_metrics:
            return {"total_operations": len(self.metrics)}
        
        durations = [m.duration for m in recent_metrics]
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        errors = sum(1 for m in recent_metrics if m.error)
        
        return {
            "total_operations": len(self.metrics),
            "recent_operations": len(recent_metrics),
            "avg_duration_ms": sum(durations) / len(durations) * 1000,
            "min_duration_ms": min(durations) * 1000,
            "max_duration_ms": max(durations) * 1000,
            "cache_hit_rate": cache_hits / len(recent_metrics) if recent_metrics else 0,
            "error_rate": errors / len(recent_metrics) if recent_metrics else 0,
            "cache_stats": self.cache.get_stats()
        }
    
    def _record_metric(self, operation_name: str, start_time: float, 
                      cache_hit: bool = False, error: Optional[str] = None) -> None:
        """Record performance metric"""
        end_time = time.time()
        duration = end_time - start_time
        
        metric = PerformanceMetrics(
            operation_name=operation_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            cache_hit=cache_hit,
            error=error
        )
        
        self.metrics.append(metric)
        
        # Keep only recent metrics
        if len(self.metrics) > self.max_metrics:
            self.metrics = self.metrics[-self.max_metrics:]

class PaginationHelper:
    """Helper class for implementing pagination"""
    
    @staticmethod
    def paginate_messages(messages: List[Any], page_size: int = 20, page: int = 1) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Paginate message list
        
        Args:
            messages: List of messages to paginate
            page_size: Number of messages per page
            page: Current page number (1-based)
            
        Returns:
            Tuple of (paginated_messages, pagination_info)
        """
        total_messages = len(messages)
        total_pages = max(1, (total_messages + page_size - 1) // page_size)
        
        # Ensure page is within bounds
        page = max(1, min(page, total_pages))
        
        # Calculate slice indices
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_messages)
        
        paginated_messages = messages[start_idx:end_idx]
        
        pagination_info = {
            "current_page": page,
            "total_pages": total_pages,
            "page_size": page_size,
            "total_items": total_messages,
            "start_index": start_idx,
            "end_index": end_idx,
            "has_previous": page > 1,
            "has_next": page < total_pages
        }
        
        return paginated_messages, pagination_info
    
    @staticmethod
    def render_pagination_controls(pagination_info: Dict[str, Any], key_prefix: str = "pagination") -> Optional[int]:
        """
        Render pagination controls in Streamlit
        
        Args:
            pagination_info: Pagination information from paginate_messages
            key_prefix: Prefix for Streamlit component keys
            
        Returns:
            New page number if changed, None otherwise
        """
        if pagination_info["total_pages"] <= 1:
            return None
        
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        new_page = pagination_info["current_page"]
        
        with col1:
            if st.button("⏮️ First", key=f"{key_prefix}_first", 
                        disabled=not pagination_info["has_previous"]):
                new_page = 1
        
        with col2:
            if st.button("◀️ Prev", key=f"{key_prefix}_prev", 
                        disabled=not pagination_info["has_previous"]):
                new_page = pagination_info["current_page"] - 1
        
        with col3:
            st.markdown(
                f"<div style='text-align: center; padding: 8px;'>"
                f"Page {pagination_info['current_page']} of {pagination_info['total_pages']} "
                f"({pagination_info['total_items']} total items)"
                f"</div>",
                unsafe_allow_html=True
            )
        
        with col4:
            if st.button("Next ▶️", key=f"{key_prefix}_next", 
                        disabled=not pagination_info["has_next"]):
                new_page = pagination_info["current_page"] + 1
        
        with col5:
            if st.button("Last ⏭️", key=f"{key_prefix}_last", 
                        disabled=not pagination_info["has_next"]):
                new_page = pagination_info["total_pages"]
        
        return new_page if new_page != pagination_info["current_page"] else None

class LoadingStateManager:
    """Manager for loading states and progress indicators"""
    
    @staticmethod
    def show_loading_spinner(message: str = "Loading..."):
        """Show loading spinner with message"""
        return st.spinner(message)
    
    @staticmethod
    def show_progress_bar(progress: float, message: str = "Processing..."):
        """Show progress bar with message"""
        progress_bar = st.progress(progress)
        st.text(message)
        return progress_bar
    
    @staticmethod
    def show_operation_status(operation_name: str, status: str = "in_progress"):
        """Show operation status indicator"""
        status_icons = {
            "in_progress": "🔄",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️"
        }
        
        icon = status_icons.get(status, "ℹ️")
        st.markdown(f"{icon} {operation_name}")
    
    @staticmethod
    def create_loading_placeholder():
        """Create placeholder for loading content"""
        return st.empty()

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()