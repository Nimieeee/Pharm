"""
Comprehensive test suite for unlimited history performance optimizations.
Tests virtual scrolling, lazy loading, chunked loading, and database optimizations.
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import streamlit as st
from typing import List, Dict, Any

# Import the modules we're testing
from unlimited_history_optimizer import (
    UnlimitedHistoryOptimizer, 
    VirtualScrollConfig, 
    MessageChunk,
    inject_unlimited_history_css
)
from message_store import Message, MessageStore
from performance_optimizer import performance_optimizer
from supabase import Client

class TestUnlimitedHistoryOptimizer:
    """Test suite for UnlimitedHistoryOptimizer"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create mock Supabase client"""
        client = Mock(spec=Client)
        return client
    
    @pytest.fixture
    def mock_message_store(self):
        """Create mock MessageStore"""
        store = Mock(spec=MessageStore)
        return store
    
    @pytest.fixture
    def optimizer(self, mock_supabase_client, mock_message_store):
        """Create UnlimitedHistoryOptimizer instance"""
        return UnlimitedHistoryOptimizer(mock_supabase_client, mock_message_store)
    
    @pytest.fixture
    def sample_messages(self):
        """Create sample messages for testing"""
        messages = []
        base_time = datetime.now()
        
        for i in range(100):
            message = Message(
                id=f"msg-{i}",
                user_id="test-user",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Test message {i} content",
                model_used="gemma2-9b-it" if i % 2 == 1 else None,
                created_at=base_time + timedelta(minutes=i),
                metadata={"test": True, "index": i}
            )
            messages.append(message)
        
        return messages
    
    def test_virtual_scroll_config_initialization(self):
        """Test VirtualScrollConfig initialization"""
        config = VirtualScrollConfig()
        
        assert config.viewport_height == 600
        assert config.item_height == 120
        assert config.buffer_size == 10
        assert config.chunk_size == 50
    
    def test_message_chunk_creation(self, sample_messages):
        """Test MessageChunk creation"""
        chunk = MessageChunk(
            messages=sample_messages[:10],
            start_index=0,
            end_index=10,
            total_count=100,
            is_cached=True,
            load_time=0.5
        )
        
        assert len(chunk.messages) == 10
        assert chunk.start_index == 0
        assert chunk.end_index == 10
        assert chunk.total_count == 100
        assert chunk.is_cached is True
        assert chunk.load_time == 0.5
    
    @patch('streamlit.session_state', {})
    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization"""
        optimizer._initialize_session_state()
        
        assert 'unlimited_history_cache' in st.session_state
        assert 'virtual_scroll_state' in st.session_state
        assert 'lazy_loading_state' in st.session_state
        
        # Check virtual scroll state structure
        vs_state = st.session_state.virtual_scroll_state
        assert 'scroll_position' in vs_state
        assert 'visible_range' in vs_state
        assert 'loaded_chunks' in vs_state
        assert 'total_messages' in vs_state
        
        # Check lazy loading state structure
        ll_state = st.session_state.lazy_loading_state
        assert 'is_loading' in ll_state
        assert 'loaded_ranges' in ll_state
        assert 'pending_ranges' in ll_state
    
    def test_get_message_count_optimized(self, optimizer, mock_supabase_client):
        """Test optimized message count retrieval"""
        # Mock database response
        mock_result = Mock()
        mock_result.count = 150
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
        
        count = optimizer._get_message_count_optimized("test-user")
        
        assert count == 150
        mock_supabase_client.table.assert_called_with('messages')
    
    def test_get_message_count_optimized_with_conversation(self, optimizer, mock_supabase_client):
        """Test optimized message count retrieval with conversation filter"""
        # Mock database response
        mock_result = Mock()
        mock_result.count = 75
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        count = optimizer._get_message_count_optimized("test-user", "conv-123")
        
        assert count == 75
    
    def test_load_message_chunk_caching(self, optimizer, mock_supabase_client, sample_messages):
        """Test message chunk loading with caching"""
        # Mock database response
        mock_result = Mock()
        mock_result.data = [
            {
                'id': msg.id,
                'user_id': msg.user_id,
                'role': msg.role,
                'content': msg.content,
                'model_used': msg.model_used,
                'created_at': msg.created_at.isoformat() + 'Z',
                'metadata': msg.metadata
            }
            for msg in sample_messages[:10]
        ]
        
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.range.return_value.execute.return_value = mock_result
        
        # First call should hit database
        messages1 = optimizer._load_message_chunk("test-user", None, 0, 10)
        assert len(messages1) == 10
        
        # Second call should hit cache
        with patch.object(performance_optimizer.cache, 'get') as mock_cache_get:
            mock_cache_get.return_value = messages1
            messages2 = optimizer._load_message_chunk("test-user", None, 0, 10)
            assert len(messages2) == 10
            mock_cache_get.assert_called_once()
    
    @patch('streamlit.session_state', {'lazy_loading_state': {'loaded_ranges': []}})
    def test_load_next_chunk(self, optimizer):
        """Test loading next chunk for lazy loading"""
        optimizer.virtual_scroll_config.chunk_size = 25
        
        # Initial state
        st.session_state.lazy_loading_state['loaded_ranges'] = [(0, 25)]
        
        # Load next chunk
        optimizer._load_next_chunk("test-user", None, 100)
        
        # Should add next range
        expected_ranges = [(0, 25), (25, 50)]
        assert st.session_state.lazy_loading_state['loaded_ranges'] == expected_ranges
    
    def test_get_unlimited_messages_optimized_cache_hit(self, optimizer, sample_messages):
        """Test unlimited messages retrieval with cache hit"""
        with patch.object(performance_optimizer, 'get_cached_user_data') as mock_cache:
            mock_cache.return_value = sample_messages
            
            messages = optimizer.get_unlimited_messages_optimized("test-user")
            
            assert len(messages) == 100
            assert messages == sample_messages
            mock_cache.assert_called_once()
    
    def test_get_unlimited_messages_optimized_cache_miss(self, optimizer, mock_supabase_client, sample_messages):
        """Test unlimited messages retrieval with cache miss"""
        # Mock cache miss
        with patch.object(performance_optimizer, 'get_cached_user_data') as mock_cache:
            mock_cache.return_value = None
            
            # Mock database response
            mock_result = Mock()
            mock_result.data = [
                {
                    'id': msg.id,
                    'user_id': msg.user_id,
                    'role': msg.role,
                    'content': msg.content,
                    'model_used': msg.model_used,
                    'created_at': msg.created_at.isoformat() + 'Z',
                    'metadata': msg.metadata
                }
                for msg in sample_messages
            ]
            
            mock_supabase_client.rpc.return_value.execute.return_value = mock_result
            
            with patch.object(performance_optimizer, 'set_cached_user_data') as mock_set_cache:
                messages = optimizer.get_unlimited_messages_optimized("test-user")
                
                assert len(messages) == 100
                mock_set_cache.assert_called_once()
    
    def test_get_unlimited_messages_optimized_with_conversation(self, optimizer, mock_supabase_client):
        """Test unlimited messages retrieval with conversation filter"""
        # Mock database response
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_client.rpc.return_value.execute.return_value = mock_result
        
        with patch.object(performance_optimizer, 'get_cached_user_data') as mock_cache:
            mock_cache.return_value = None
            
            messages = optimizer.get_unlimited_messages_optimized("test-user", "conv-123")
            
            # Should call conversation-specific RPC function
            mock_supabase_client.rpc.assert_called_with('get_conversation_messages_unlimited', {
                'user_id': 'test-user',
                'conversation_id': 'conv-123'
            })
    
    @patch('streamlit.markdown')
    @patch('streamlit.container')
    def test_render_virtual_scrolled_messages(self, mock_container, mock_markdown, optimizer, sample_messages):
        """Test virtual scrolled message rendering"""
        with patch('streamlit.session_state', {
            'virtual_scroll_state': {
                'scroll_position': 0,
                'visible_range': (0, 50),
                'loaded_chunks': {},
                'total_messages': 0
            }
        }):
            optimizer.render_virtual_scrolled_messages(sample_messages, container_height=600)
            
            # Should call markdown for container setup
            assert mock_markdown.call_count >= 2  # Top spacer, bottom spacer, container
            mock_container.assert_called()
    
    @patch('streamlit.info')
    def test_render_virtual_scrolled_messages_empty(self, mock_info, optimizer):
        """Test virtual scrolled message rendering with empty messages"""
        optimizer.render_virtual_scrolled_messages([], container_height=600)
        mock_info.assert_called_with("No messages to display")
    
    @patch('streamlit.session_state', {
        'lazy_loading_state': {
            'loaded_ranges': [],
            'is_loading': False,
            'pending_ranges': []
        }
    })
    @patch('streamlit.markdown')
    @patch('streamlit.caption')
    @patch('streamlit.info')
    def test_render_lazy_loaded_messages_empty(self, mock_info, mock_caption, mock_markdown, optimizer):
        """Test lazy loaded message rendering with no messages"""
        with patch.object(optimizer, '_get_message_count_optimized') as mock_count:
            mock_count.return_value = 0
            
            optimizer.render_lazy_loaded_messages("test-user")
            
            mock_info.assert_called_with("No messages to display")
    
    @patch('streamlit.session_state', {
        'lazy_loading_state': {
            'loaded_ranges': [],
            'is_loading': False,
            'pending_ranges': []
        }
    })
    @patch('streamlit.markdown')
    @patch('streamlit.caption')
    @patch('streamlit.button')
    def test_render_lazy_loaded_messages_with_load_more(self, mock_button, mock_caption, mock_markdown, optimizer, sample_messages):
        """Test lazy loaded message rendering with load more button"""
        mock_button.return_value = False  # Button not clicked
        
        with patch.object(optimizer, '_get_message_count_optimized') as mock_count:
            mock_count.return_value = 100
            
            with patch.object(optimizer, '_load_message_chunk') as mock_load_chunk:
                mock_load_chunk.return_value = sample_messages[:50]
                
                optimizer.render_lazy_loaded_messages("test-user", initial_load_count=50)
                
                # Should show load more button since 50 < 100
                mock_button.assert_called()
                button_call_args = mock_button.call_args[0][0]
                assert "Load More Messages" in button_call_args
                assert "50 remaining" in button_call_args
    
    @patch('streamlit.progress')
    @patch('streamlit.empty')
    @patch('streamlit.markdown')
    @patch('streamlit.caption')
    @patch('streamlit.success')
    @patch('time.sleep')
    def test_render_chunked_unlimited_history(self, mock_sleep, mock_success, mock_caption, 
                                            mock_markdown, mock_empty, mock_progress, 
                                            optimizer, sample_messages):
        """Test chunked unlimited history rendering"""
        # Mock progress components
        mock_progress_bar = Mock()
        mock_progress.return_value = mock_progress_bar
        mock_status_text = Mock()
        mock_empty.return_value = mock_status_text
        
        with patch.object(optimizer, '_get_message_count_optimized') as mock_count:
            mock_count.return_value = 100
            
            with patch.object(optimizer, '_load_message_chunk') as mock_load_chunk:
                mock_load_chunk.return_value = sample_messages[:50]  # Return chunk
                
                with patch.object(optimizer, '_inject_auto_scroll_script') as mock_scroll:
                    optimizer.render_chunked_unlimited_history("test-user")
                    
                    # Should show progress updates
                    mock_progress_bar.progress.assert_called()
                    mock_status_text.text.assert_called()
                    
                    # Should show success message
                    mock_success.assert_called()
                    
                    # Should inject auto-scroll
                    mock_scroll.assert_called_once()
    
    def test_get_performance_metrics(self, optimizer):
        """Test performance metrics retrieval"""
        with patch.object(performance_optimizer.cache, 'get_stats') as mock_stats:
            mock_stats.return_value = {
                "total_entries": 10,
                "hit_rate": 0.75,
                "memory_usage_mb": 5.2
            }
            
            with patch('streamlit.session_state', {'unlimited_history_cache': {'key1': 'value1'}}):
                metrics = optimizer.get_performance_metrics()
                
                assert metrics["cache_entries"] == 10
                assert metrics["cache_hit_rate"] == 0.75
                assert metrics["memory_usage_mb"] == 5.2
                assert metrics["session_state_size"] == 1
                assert "virtual_scroll_config" in metrics
    
    @patch('streamlit.session_state', {
        'unlimited_history_cache': {'unlimited_messages:test-user:all': 'data'},
        'virtual_scroll_state': {'scroll_position': 10},
        'lazy_loading_state': {'loaded_ranges': [(0, 50)]}
    })
    def test_clear_unlimited_history_cache_user_specific(self, optimizer):
        """Test clearing cache for specific user"""
        with patch.object(performance_optimizer, 'invalidate_user_cache') as mock_invalidate:
            optimizer.clear_unlimited_history_cache("test-user")
            
            mock_invalidate.assert_called_with("test-user")
            
            # Should reset session state
            assert st.session_state.virtual_scroll_state['scroll_position'] == 0
            assert st.session_state.lazy_loading_state['loaded_ranges'] == []
    
    @patch('streamlit.session_state', {
        'unlimited_history_cache': {'key1': 'value1'},
        'virtual_scroll_state': {'scroll_position': 10},
        'lazy_loading_state': {'loaded_ranges': [(0, 50)]}
    })
    def test_clear_unlimited_history_cache_all(self, optimizer):
        """Test clearing all cache"""
        with patch.object(performance_optimizer.cache, 'clear') as mock_clear:
            optimizer.clear_unlimited_history_cache()
            
            mock_clear.assert_called_once()
            
            # Should reset all session state
            assert st.session_state.unlimited_history_cache == {}
            assert st.session_state.virtual_scroll_state['scroll_position'] == 0
            assert st.session_state.lazy_loading_state['loaded_ranges'] == []

class TestPerformanceWithLargeDatasets:
    """Test performance with large datasets"""
    
    @pytest.fixture
    def large_message_set(self):
        """Create large message set for performance testing"""
        messages = []
        base_time = datetime.now()
        
        for i in range(5000):  # 5000 messages
            message = Message(
                id=f"msg-{i:05d}",
                user_id="test-user",
                role="user" if i % 2 == 0 else "assistant",
                content=f"Performance test message {i} with longer content to simulate real usage patterns. " * 3,
                model_used="gemma2-9b-it" if i % 2 == 1 else None,
                created_at=base_time + timedelta(seconds=i * 30),
                metadata={"test": True, "index": i, "batch": i // 100}
            )
            messages.append(message)
        
        return messages
    
    def test_chunked_loading_performance(self, large_message_set):
        """Test performance of chunked loading with large dataset"""
        chunk_size = 50
        total_messages = len(large_message_set)
        
        start_time = time.time()
        
        # Simulate chunked loading
        chunks_loaded = 0
        for chunk_start in range(0, total_messages, chunk_size):
            chunk_end = min(chunk_start + chunk_size, total_messages)
            chunk = large_message_set[chunk_start:chunk_end]
            chunks_loaded += 1
            
            # Simulate processing time
            time.sleep(0.001)  # 1ms per chunk
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in reasonable time
        assert total_time < 1.0  # Less than 1 second
        assert chunks_loaded == (total_messages + chunk_size - 1) // chunk_size
    
    def test_virtual_scrolling_calculations(self, large_message_set):
        """Test virtual scrolling calculations with large dataset"""
        config = VirtualScrollConfig(
            viewport_height=600,
            item_height=120,
            buffer_size=10,
            chunk_size=50
        )
        
        total_messages = len(large_message_set)
        viewport_items = config.viewport_height // config.item_height
        
        # Test different scroll positions
        scroll_positions = [0, 100, 500, 1000, 2000, 4000]
        
        for scroll_pos in scroll_positions:
            start_index = max(0, scroll_pos - config.buffer_size)
            end_index = min(total_messages, scroll_pos + viewport_items + config.buffer_size)
            
            # Ensure valid range
            assert start_index >= 0
            assert end_index <= total_messages
            assert start_index <= end_index
            
            # Ensure reasonable buffer size
            visible_items = end_index - start_index
            assert visible_items <= viewport_items + (2 * config.buffer_size)
    
    def test_memory_usage_estimation(self, large_message_set):
        """Test memory usage estimation for large datasets"""
        import sys
        
        # Estimate memory usage of message objects
        single_message_size = sys.getsizeof(large_message_set[0])
        total_estimated_size = single_message_size * len(large_message_set)
        
        # Should be reasonable for 5000 messages
        assert total_estimated_size < 50 * 1024 * 1024  # Less than 50MB
        
        # Test chunked memory usage
        chunk_size = 50
        chunk_memory = single_message_size * chunk_size
        
        # Single chunk should be very manageable
        assert chunk_memory < 1024 * 1024  # Less than 1MB per chunk

class TestDatabaseOptimizations:
    """Test database optimization functions"""
    
    @pytest.fixture
    def mock_supabase_client(self):
        """Create mock Supabase client for database tests"""
        client = Mock(spec=Client)
        return client
    
    def test_unlimited_messages_rpc_call(self, mock_supabase_client):
        """Test RPC call for unlimited messages"""
        # Mock RPC response
        mock_result = Mock()
        mock_result.data = [
            {
                'id': 'msg-1',
                'user_id': 'test-user',
                'role': 'user',
                'content': 'Test message',
                'model_used': None,
                'created_at': '2024-01-01T12:00:00Z',
                'metadata': {},
                'conversation_id': 'conv-1'
            }
        ]
        mock_supabase_client.rpc.return_value.execute.return_value = mock_result
        
        optimizer = UnlimitedHistoryOptimizer(mock_supabase_client, Mock())
        messages = optimizer._get_all_user_messages_optimized("test-user")
        
        # Should call the optimized RPC function
        mock_supabase_client.rpc.assert_called_with('get_all_user_messages_unlimited', {
            'user_id': 'test-user'
        })
        
        assert len(messages) == 1
        assert messages[0].id == 'msg-1'
    
    def test_conversation_messages_rpc_call(self, mock_supabase_client):
        """Test RPC call for conversation messages"""
        # Mock RPC response
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_client.rpc.return_value.execute.return_value = mock_result
        
        optimizer = UnlimitedHistoryOptimizer(mock_supabase_client, Mock())
        messages = optimizer._get_conversation_messages_optimized("test-user", "conv-123")
        
        # Should call the conversation-specific RPC function
        mock_supabase_client.rpc.assert_called_with('get_conversation_messages_unlimited', {
            'user_id': 'test-user',
            'conversation_id': 'conv-123'
        })
    
    def test_fallback_to_direct_query(self, mock_supabase_client):
        """Test fallback to direct query when RPC fails"""
        # Mock RPC failure
        mock_supabase_client.rpc.return_value.execute.side_effect = Exception("RPC not found")
        
        # Mock direct query success
        mock_result = Mock()
        mock_result.data = []
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
        
        optimizer = UnlimitedHistoryOptimizer(mock_supabase_client, Mock())
        
        # Should fallback to message store method
        with patch.object(optimizer.message_store, 'get_conversation_history') as mock_fallback:
            mock_fallback.return_value = []
            messages = optimizer._get_all_user_messages_optimized("test-user")
            mock_fallback.assert_called_once()

def test_inject_unlimited_history_css():
    """Test CSS injection for unlimited history"""
    with patch('streamlit.markdown') as mock_markdown:
        inject_unlimited_history_css()
        
        mock_markdown.assert_called_once()
        css_content = mock_markdown.call_args[0][0]
        
        # Should contain key CSS classes
        assert '.unlimited-history-container' in css_content
        assert '.virtual-scroll-container' in css_content
        assert '.lazy-load-container' in css_content
        assert '.message-bubble.optimized' in css_content
        assert 'contain: layout style paint' in css_content  # Performance optimization
        assert 'will-change: scroll-position' in css_content  # Performance optimization

if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short"])