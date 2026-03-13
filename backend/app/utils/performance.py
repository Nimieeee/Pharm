"""
Performance monitoring utilities for PharmGPT Backend
Provides timing, logging, and diagnostics for all operations
"""

import time
import functools
from typing import Callable, Any
from contextlib import contextmanager

# Global timing storage for request-level aggregation
_request_timings = {}


class PerformanceMonitor:
    """Performance monitoring for request lifecycle"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.checkpoints = []
    
    def start(self):
        self.start_time = time.time()
        print(f"⏱️ [{self.operation_name}] Started")
        return self
    
    def checkpoint(self, label: str):
        if self.start_time:
            elapsed = (time.time() - self.start_time) * 1000
            self.checkpoints.append((label, elapsed))
            print(f"  ⏱️ [{self.operation_name}] {label}: {elapsed:.1f}ms")
    
    def finish(self):
        if self.start_time:
            total = (time.time() - self.start_time) * 1000
            print(f"✅ [{self.operation_name}] Completed in {total:.1f}ms")
            if total > 5000:
                print(f"⚠️ SLOW OPERATION: {self.operation_name} took {total:.1f}ms")
            return total
        return 0


@contextmanager
def timed_operation(name: str):
    """Context manager for timing operations"""
    start = time.time()
    print(f"⏱️ [{name}] Started...")
    try:
        yield
    finally:
        elapsed = (time.time() - start) * 1000
        if elapsed > 1000:
            print(f"🐢 [{name}] SLOW: {elapsed:.1f}ms")
        elif elapsed > 100:
            print(f"⏱️ [{name}] {elapsed:.1f}ms")
        else:
            print(f"⚡ [{name}] {elapsed:.1f}ms")


def timed(func: Callable) -> Callable:
    """Decorator to time async functions"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        func_name = func.__name__
        try:
            result = await func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000
            if elapsed > 1000:
                print(f"🐢 [{func_name}] SLOW: {elapsed:.1f}ms")
            elif elapsed > 100:
                print(f"⏱️ [{func_name}] {elapsed:.1f}ms")
            return result
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ [{func_name}] Failed after {elapsed:.1f}ms: {str(e)}")
            raise
    return wrapper


def timed_sync(func: Callable) -> Callable:
    """Decorator to time sync functions"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start = time.time()
        func_name = func.__name__
        try:
            result = func(*args, **kwargs)
            elapsed = (time.time() - start) * 1000
            if elapsed > 1000:
                print(f"🐢 [{func_name}] SLOW: {elapsed:.1f}ms")
            elif elapsed > 100:
                print(f"⏱️ [{func_name}] {elapsed:.1f}ms")
            return result
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ [{func_name}] Failed after {elapsed:.1f}ms: {str(e)}")
            raise
    return wrapper


def log_db_query(query_name: str, start_time: float, row_count: int = 0):
    """Log database query performance"""
    elapsed = (time.time() - start_time) * 1000
    if elapsed > 500:
        print(f"🐌 DB SLOW [{query_name}]: {elapsed:.1f}ms, rows={row_count}")
    else:
        print(f"📊 DB [{query_name}]: {elapsed:.1f}ms, rows={row_count}")
