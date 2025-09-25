"""
Test suite for performance optimizations
"""

import pytest
import time
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from performance_optimizer import MemoryCache, PerformanceOptimizer, PaginationHelper
from message_store_optimized import OptimizedMessageStore, MessagePage
from performance_monitor import PerformanceMonitor

# Mock environment variables for testing
os.environ['SUPABASE_URL'] = 'test'
os.environ['SUPABASE_ANON_KEY'] = 'test'

# Import after setting environment variables
from vector_search_optimizer import VectorSearchOptimizer, SearchResult

class TestMemoryCache:
    """Test memory cache functionality"""
    
    def test_cache_basic_operations(self):
        """Test basic cache operations"""
        cache = MemoryCache(max_size=10, default_ttl=60)
        
        # Test set and get
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Test non-existent key
        assert cache.get("nonexistent") is None
        
        # Test delete
        assert cache.delete("key1") is True
        assert cache.get("key1") is None
        assert cache.delete("nonexistent") is False
    
    def test_cache_expiration(self):
        """Test cache expiration"""
        cache = MemoryCache(max_size=10, default_ttl=1)  # 1 second TTL
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None
    
    def test_cache_size_limit(self):
        """Test cache size limit and LRU eviction"""
        cache = MemoryCache(max_size=3, default_ttl=60)
        
        # Fill cache to capacity
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # Add one more to trigger eviction
        cache.set("key4", "value4")
        
        # key1 should be evicted (LRU)
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"
    
    def test_cache_stats(self):
        """Test cache statistics"""
        cache = MemoryCache(max_size=10, default_ttl=60)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["max_size"] == 10
        assert "memory_usage_mb" in stats

class TestPerformanceOptimizer:
    """Test performance optimizer functionality"""
    
    def test_cached_operation_decorator(self):
        """Test cached operation decorator"""
        optimizer = PerformanceOptimizer()
        call_count = 0
        
        @optimizer.cached_operation("test_key", ttl=60)
        def expensive_operation(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # First call should execute function
        result1 = expensive_operation(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_operation(5)
        assert result2 == 10
        assert call_count == 1  # Function not called again
    
    def test_user_data_caching(self):
        """Test user-specific data caching"""
        optimizer = PerformanceOptimizer()
        
        user_id = "test_user"
        data_type = "messages"
        test_data = {"messages": [1, 2, 3]}
        
        # Set cached data
        optimizer.set_cached_user_data(user_id, data_type, test_data)
        
        # Get cached data
        cached_data = optimizer.get_cached_user_data(user_id, data_type)
        assert cached_data == test_data
        
        # Invalidate user cache
        optimizer.invalidate_user_cache(user_id)
        cached_data = optimizer.get_cached_user_data(user_id, data_type)
        assert cached_data is None

class TestPaginationHelper:
    """Test pagination helper functionality"""
    
    def test_paginate_messages(self):
        """Test message pagination"""
        messages = [f"message_{i}" for i in range(25)]  # 25 messages
        
        # Test first page
        paginated, info = PaginationHelper.paginate_messages(messages, page_size=10, page=1)
        assert len(paginated) == 10
        assert paginated[0] == "message_0"
        assert info["current_page"] == 1
        assert info["total_pages"] == 3
        assert info["has_next"] is True
        assert info["has_previous"] is False
        
        # Test middle page
        paginated, info = PaginationHelper.paginate_messages(messages, page_size=10, page=2)
        assert len(paginated) == 10
        assert paginated[0] == "message_10"
        assert info["current_page"] == 2
        assert info["has_next"] is True
        assert info["has_previous"] is True
        
        # Test last page
        paginated, info = PaginationHelper.paginate_messages(messages, page_size=10, page=3)
        assert len(paginated) == 5  # Remaining messages
        assert paginated[0] == "message_20"
        assert info["current_page"] == 3
        assert info["has_next"] is False
        assert info["has_previous"] is True
    
    def test_pagination_edge_cases(self):
        """Test pagination edge cases"""
        messages = ["msg1", "msg2"]
        
        # Test page beyond range
        paginated, info = PaginationHelper.paginate_messages(messages, page_size=10, page=5)
        assert len(paginated) == 2  # Should return all messages
        assert info["current_page"] == 1  # Should clamp to valid page
        
        # Test empty list
        paginated, info = PaginationHelper.paginate_messages([], page_size=10, page=1)
        assert len(paginated) == 0
        assert info["total_pages"] == 1
        assert info["total_items"] == 0

class TestOptimizedMessageStore:
    """Test optimized message store functionality"""
    
    @patch('message_store_optimized.performance_optimizer')
    def test_get_paginated_messages_with_cache(self, mock_optimizer):
        """Test paginated message retrieval with caching"""
        # Mock Supabase client
        mock_client = Mock()
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.offset.return_value.execute.return_value.data = [
            {
                'id': 'msg1',
                'user_id': 'user1',
                'role': 'user',
                'content': 'Hello',
                'model_used': None,
                'created_at': '2024-01-01T12:00:00Z',
                'metadata': {}
            }
        ]
        
        # Mock cache miss
        mock_optimizer.get_cached_user_data.return_value = None
        
        store = OptimizedMessageStore(mock_client)
        
        # Mock get_cached_message_count
        with patch.object(store, 'get_cached_message_count', return_value=1):
            result = store.get_paginated_messages("user1", page=1, page_size=20)
        
        assert isinstance(result, MessagePage)
        assert len(result.messages) == 1
        assert result.messages[0].content == "Hello"
        assert result.pagination_info["current_page"] == 1
        assert result.total_count == 1
        
        # Verify cache was called
        mock_optimizer.set_cached_user_data.assert_called_once()

class TestVectorSearchOptimizer:
    """Test vector search optimizer functionality"""
    
    @patch('vector_search_optimizer.performance_optimizer')
    def test_optimized_similarity_search_with_cache(self, mock_optimizer):
        """Test optimized similarity search with caching"""
        # Mock Supabase client
        mock_client = Mock()
        mock_client.rpc.return_value.execute.return_value.data = [
            {
                'id': 'doc1',
                'content': 'Test document content',
                'source': 'test.pdf',
                'metadata': {},
                'similarity': 0.8
            }
        ]
        
        # Mock cache miss
        mock_optimizer.get_cached_user_data.return_value = None
        
        # Mock embedding model
        mock_embedding_model = Mock()
        mock_embedding_model.embed_query.return_value = [0.1] * 384
        
        optimizer = VectorSearchOptimizer(mock_client, mock_embedding_model)
        
        # Mock _get_user_document_count_cached
        with patch.object(optimizer, '_get_user_document_count_cached', return_value=1):
            result = optimizer.optimized_similarity_search("test query", "user1", k=5)
        
        assert isinstance(result, SearchResult)
        assert len(result.documents) == 1
        assert result.documents[0].content == "Test document content"
        assert result.search_time_ms > 0
        assert result.total_documents_searched == 1
        
        # Verify cache was called
        mock_optimizer.set_cached_user_data.assert_called()

class TestPerformanceMonitor:
    """Test performance monitor functionality"""
    
    def test_collect_system_metrics(self):
        """Test system metrics collection"""
        monitor = PerformanceMonitor()
        
        metrics = monitor.collect_system_metrics()
        
        assert metrics.cpu_percent >= 0
        assert metrics.memory_percent >= 0
        assert metrics.memory_used_mb >= 0
        assert metrics.memory_available_mb >= 0
        assert isinstance(metrics.timestamp, datetime)
    
    def test_collect_app_metrics(self):
        """Test application metrics collection"""
        monitor = PerformanceMonitor()
        
        with patch('performance_monitor.performance_optimizer') as mock_optimizer:
            mock_optimizer.get_performance_stats.return_value = {
                'total_operations': 100,
                'avg_duration_ms': 250.0,
                'cache_hit_rate': 0.75,
                'error_rate': 0.02
            }
            
            metrics = monitor.collect_app_metrics()
        
        assert metrics.total_requests == 100
        assert metrics.avg_response_time_ms == 250.0
        assert metrics.cache_hit_rate == 0.75
        assert metrics.error_rate == 0.02
        assert isinstance(metrics.timestamp, datetime)
    
    def test_performance_alerts(self):
        """Test performance alert generation"""
        monitor = PerformanceMonitor()
        
        # Create metrics that should trigger alerts
        from performance_monitor import SystemMetrics, AppMetrics
        
        system_metrics = SystemMetrics(
            cpu_percent=95.0,  # Critical
            memory_percent=85.0,  # Warning
            memory_used_mb=8000,
            memory_available_mb=1000,
            timestamp=datetime.now()
        )
        
        app_metrics = AppMetrics(
            active_users=1,
            total_requests=100,
            avg_response_time_ms=6000.0,  # Critical
            cache_hit_rate=0.5,
            error_rate=0.08,  # Warning
            timestamp=datetime.now()
        )
        
        alerts = monitor.check_performance_alerts(system_metrics, app_metrics)
        
        # Should have 4 alerts: CPU critical, memory warning, response time critical, error rate warning
        assert len(alerts) == 4
        
        alert_types = [alert["type"] for alert in alerts]
        assert "critical" in alert_types
        assert "warning" in alert_types
        
        alert_categories = [alert["category"] for alert in alerts]
        assert "cpu" in alert_categories
        assert "memory" in alert_categories
        assert "response_time" in alert_categories
        assert "error_rate" in alert_categories

def test_integration_performance_optimization():
    """Integration test for performance optimization features"""
    # Test that all components work together
    optimizer = PerformanceOptimizer()
    monitor = PerformanceMonitor()
    
    # Test caching workflow
    test_data = {"key": "value", "timestamp": datetime.now().isoformat()}
    optimizer.set_cached_user_data("test_user", "test_data", test_data)
    
    cached_result = optimizer.get_cached_user_data("test_user", "test_data")
    assert cached_result == test_data
    
    # Test performance monitoring
    system_metrics = monitor.collect_system_metrics()
    app_metrics = monitor.collect_app_metrics()
    
    assert system_metrics is not None
    assert app_metrics is not None
    
    # Test optimization
    optimization_result = monitor.optimize_performance()
    assert optimization_result["success"] is True

if __name__ == "__main__":
    # Run basic tests
    test_cache = TestMemoryCache()
    test_cache.test_cache_basic_operations()
    test_cache.test_cache_size_limit()
    
    test_optimizer = TestPerformanceOptimizer()
    test_optimizer.test_user_data_caching()
    
    test_pagination = TestPaginationHelper()
    test_pagination.test_paginate_messages()
    test_pagination.test_pagination_edge_cases()
    
    test_monitor = TestPerformanceMonitor()
    test_monitor.test_collect_system_metrics()
    
    test_integration_performance_optimization()
    
    print("✅ All performance optimization tests passed!")