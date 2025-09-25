"""
Optimized Chat Interface with pagination, loading states, and performance improvements
"""

import streamlit as st
from typing import List, Dict, Any, Optional, Generator, Union
from dataclasses import dataclass
from datetime import datetime
import time
import io
import base64
from pathlib import Path

from message_store import Message
from message_store_optimized import MessagePage, OptimizedMessageStore
from theme_manager import ThemeManager
from performance_optimizer import performance_optimizer, PaginationHelper, LoadingStateManager
from chat_interface import ChatInterface, StreamingMessage

class OptimizedChatInterface(ChatInterface):
    """Enhanced chat interface with pagination, loading states, and performance optimizations"""
    
    def __init__(self, theme_manager: ThemeManager, message_store: Optional[OptimizedMessageStore] = None):
        super().__init__(theme_manager)
        self.message_store = message_store
        self.page_size = 20  # Messages per page
        self._initialize_pagination_state()
    
    def _initialize_pagination_state(self):
        """Initialize pagination-related session state"""
        if 'chat_current_page' not in st.session_state:
            st.session_state.chat_current_page = 1
        if 'chat_page_size' not in st.session_state:
            st.session_state.chat_page_size = self.page_size
        if 'chat_total_pages' not in st.session_state:
            st.session_state.chat_total_pages = 1
        if 'loading_states' not in st.session_state:
            st.session_state.loading_states = {}
    
    def render_paginated_chat_history(self, user_id: str, show_pagination: bool = True) -> None:
        """
        Render paginated chat history with loading states
        
        Args:
            user_id: User's unique identifier
            show_pagination: Whether to show pagination controls
        """
        if not self.message_store:
            st.error("Message store not available")
            return
        
        # Show loading state
        with LoadingStateManager.show_loading_spinner("Loading conversation history..."):
            # Get paginated messages
            message_page = self.message_store.get_paginated_messages(
                user_id=user_id,
                page=st.session_state.chat_current_page,
                page_size=st.session_state.chat_page_size
            )
        
        # Update session state with pagination info
        st.session_state.chat_total_pages = message_page.pagination_info.get("total_pages", 1)
        
        # Show cache hit indicator for debugging
        if message_page.cache_hit:
            st.caption("📋 Loaded from cache")
        
        # Render pagination controls at top if enabled and multiple pages
        if show_pagination and message_page.pagination_info.get("total_pages", 1) > 1:
            self._render_top_pagination_controls(message_page.pagination_info)
        
        # Render messages
        if not message_page.messages and not st.session_state.show_typing_indicator:
            self._render_welcome_message()
        else:
            # Create container for messages
            chat_container = st.container()
            
            with chat_container:
                # Render messages in chronological order for the current page
                for message in reversed(message_page.messages):  # Reverse to show oldest first
                    self._render_message_bubble(message)
                
                # Render streaming message if active
                if st.session_state.streaming_message:
                    self._render_streaming_message(st.session_state.streaming_message)
                
                # Render typing indicator if active
                elif st.session_state.show_typing_indicator:
                    self._render_typing_indicator()
        
        # Render pagination controls at bottom if enabled and multiple pages
        if show_pagination and message_page.pagination_info.get("total_pages", 1) > 1:
            self._render_bottom_pagination_controls(message_page.pagination_info)
        
        # Auto-scroll to bottom for first page (most recent messages)
        if st.session_state.chat_current_page == 1:
            self._inject_auto_scroll_script()
    
    def render_conversation_controls_optimized(self, user_id: str, chat_manager) -> Dict[str, bool]:
        """
        Render optimized conversation management controls with loading states
        
        Args:
            user_id: Current user ID
            chat_manager: ChatManager instance
            
        Returns:
            Dictionary of control actions triggered
        """
        st.markdown("### 💬 Conversation Controls")
        
        # Get conversation stats with caching
        if self.message_store:
            with st.spinner("Loading conversation statistics..."):
                stats = self.message_store.get_message_statistics(user_id)
        else:
            stats = chat_manager.get_user_message_stats(user_id) if chat_manager else {}
        
        # Display enhanced statistics
        self._render_enhanced_statistics(stats)
        
        controls = {}
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            controls['clear'] = st.button(
                "🗑️ Clear Chat",
                key="clear_conversation_optimized",
                use_container_width=True,
                help="Delete all messages in this conversation"
            )
        
        with col2:
            controls['export'] = st.button(
                "📥 Export",
                key="export_conversation_optimized", 
                use_container_width=True,
                help="Export conversation history"
            )
        
        with col3:
            controls['refresh'] = st.button(
                "🔄 Refresh",
                key="refresh_conversation",
                use_container_width=True,
                help="Refresh conversation and clear cache"
            )
        
        # Handle refresh action
        if controls['refresh']:
            self._handle_refresh_action(user_id)
            st.rerun()
        
        # Confirmation dialog for clear action
        if controls['clear']:
            controls['clear_confirmed'] = self._render_clear_confirmation_dialog()
        else:
            controls['clear_confirmed'] = False
        
        return controls
    
    def render_performance_dashboard(self) -> None:
        """Render performance monitoring dashboard"""
        st.markdown("### 📊 Performance Dashboard")
        
        # Get performance stats
        perf_stats = performance_optimizer.get_performance_stats()
        
        if perf_stats.get("total_operations", 0) == 0:
            st.info("No performance data available yet")
            return
        
        # Display performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Avg Response Time", 
                f"{perf_stats.get('avg_duration_ms', 0):.1f}ms"
            )
        
        with col2:
            st.metric(
                "Cache Hit Rate", 
                f"{perf_stats.get('cache_hit_rate', 0):.1%}"
            )
        
        with col3:
            st.metric(
                "Total Operations", 
                perf_stats.get('total_operations', 0)
            )
        
        with col4:
            st.metric(
                "Error Rate", 
                f"{perf_stats.get('error_rate', 0):.1%}"
            )
        
        # Cache statistics
        cache_stats = perf_stats.get('cache_stats', {})
        if cache_stats:
            st.markdown("#### Cache Statistics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Cache Entries", cache_stats.get('total_entries', 0))
            
            with col2:
                st.metric("Memory Usage", f"{cache_stats.get('memory_usage_mb', 0):.1f}MB")
            
            with col3:
                if st.button("Clear Cache", key="clear_cache_btn"):
                    performance_optimizer.cache.clear()
                    st.success("Cache cleared!")
                    st.rerun()
    
    def render_loading_message_input(self, placeholder: str = "Ask about pharmacology...", 
                                   enable_attachments: bool = True) -> Dict[str, Any]:
        """
        Render message input with loading state management
        
        Args:
            placeholder: Placeholder text for input
            enable_attachments: Whether to enable file attachments
            
        Returns:
            Dictionary with 'message' and 'files' if submitted, empty dict otherwise
        """
        # Check if any operation is in progress
        is_loading = any(st.session_state.loading_states.values())
        
        # Show loading indicator if operations are in progress
        if is_loading:
            st.info("🔄 Processing your request... Please wait.")
        
        # Render input with disabled state during loading
        return self.render_message_input_with_attachments(
            placeholder=placeholder if not is_loading else "Please wait...",
            enable_attachments=enable_attachments and not is_loading
        )
    
    def set_loading_state(self, operation: str, is_loading: bool) -> None:
        """
        Set loading state for an operation
        
        Args:
            operation: Name of the operation
            is_loading: Whether the operation is loading
        """
        if 'loading_states' not in st.session_state:
            st.session_state.loading_states = {}
        
        st.session_state.loading_states[operation] = is_loading
    
    def is_any_operation_loading(self) -> bool:
        """Check if any operation is currently loading"""
        return any(st.session_state.loading_states.values())
    
    def render_streaming_response_optimized(self, response_generator: Generator[str, None, None], 
                                          operation_name: str = "Generating response") -> str:
        """
        Render streaming response with optimized performance tracking
        
        Args:
            response_generator: Generator yielding response chunks
            operation_name: Name of the operation for tracking
            
        Returns:
            Complete response text
        """
        # Set loading state
        self.set_loading_state(operation_name, True)
        
        # Create placeholder for streaming content
        response_placeholder = st.empty()
        collected_response = ""
        
        # Track performance
        start_time = time.time()
        chunk_count = 0
        
        try:
            # Start streaming
            self.start_streaming_response()
            
            for chunk in response_generator:
                collected_response += chunk
                chunk_count += 1
                
                # Update streaming message
                self.update_streaming_message(chunk)
                
                # Update display with cursor
                response_placeholder.markdown(collected_response + "▌")
                
                # Yield control periodically to prevent blocking
                if chunk_count % 10 == 0:
                    time.sleep(0.01)
            
            # Complete streaming
            final_response = self.complete_streaming_message()
            response_placeholder.markdown(final_response)
            
            # Record performance metrics
            duration = time.time() - start_time
            performance_optimizer._record_metric(
                operation_name=operation_name,
                start_time=start_time,
                cache_hit=False
            )
            
            logger.info(f"Streaming completed: {chunk_count} chunks in {duration:.2f}s")
            
            return final_response
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_msg = "Sorry, I encountered an error while generating the response."
            response_placeholder.error(error_msg)
            return error_msg
            
        finally:
            # Clear loading state
            self.set_loading_state(operation_name, False)
    
    def _render_top_pagination_controls(self, pagination_info: Dict[str, Any]) -> None:
        """Render pagination controls at the top"""
        st.markdown("#### 📄 Conversation History")
        
        new_page = PaginationHelper.render_pagination_controls(
            pagination_info, 
            key_prefix="chat_top"
        )
        
        if new_page:
            st.session_state.chat_current_page = new_page
            st.rerun()
    
    def _render_bottom_pagination_controls(self, pagination_info: Dict[str, Any]) -> None:
        """Render pagination controls at the bottom"""
        st.markdown("---")
        
        new_page = PaginationHelper.render_pagination_controls(
            pagination_info, 
            key_prefix="chat_bottom"
        )
        
        if new_page:
            st.session_state.chat_current_page = new_page
            st.rerun()
    
    def _render_enhanced_statistics(self, stats: Dict[str, Any]) -> None:
        """Render enhanced conversation statistics"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Messages", stats.get('total_messages', 0))
        
        with col2:
            st.metric("Recent (24h)", stats.get('recent_messages', 0))
        
        with col3:
            avg_per_day = stats.get('avg_messages_per_day', 0)
            st.metric("Avg/Day", f"{avg_per_day:.1f}")
        
        # Model usage breakdown
        models_used = stats.get('models_used', {})
        if models_used:
            st.markdown("**Model Usage:**")
            for model, count in models_used.items():
                if model and model != 'unknown':
                    model_display = "🚀 Fast" if "gemma" in model.lower() else "⭐ Premium"
                    st.write(f"• {model_display}: {count} responses")
        
        # Activity information
        if stats.get('first_message_date'):
            first_date = datetime.fromisoformat(stats['first_message_date']).strftime("%Y-%m-%d")
            st.caption(f"First message: {first_date}")
    
    def _handle_refresh_action(self, user_id: str) -> None:
        """Handle refresh action - clear caches and reset pagination"""
        # Clear user-specific caches
        performance_optimizer.invalidate_user_cache(user_id)
        
        # Reset pagination to first page
        st.session_state.chat_current_page = 1
        
        # Clear any loading states
        st.session_state.loading_states = {}
        
        st.success("🔄 Conversation refreshed and cache cleared!")
    
    def render_page_size_selector(self) -> None:
        """Render page size selector for pagination"""
        st.markdown("#### ⚙️ Display Settings")
        
        page_size_options = [10, 20, 50, 100]
        current_page_size = st.session_state.get('chat_page_size', 20)
        
        new_page_size = st.selectbox(
            "Messages per page:",
            options=page_size_options,
            index=page_size_options.index(current_page_size) if current_page_size in page_size_options else 1,
            key="page_size_selector"
        )
        
        if new_page_size != current_page_size:
            st.session_state.chat_page_size = new_page_size
            st.session_state.chat_current_page = 1  # Reset to first page
            st.rerun()

def inject_optimized_chat_css() -> None:
    """Inject optimized CSS for enhanced chat interface"""
    css = """
    <style>
    /* Performance optimizations */
    .message-bubble {
        will-change: transform;
        transform: translateZ(0);
    }
    
    /* Loading states */
    .loading-overlay {
        position: relative;
        opacity: 0.6;
        pointer-events: none;
    }
    
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(0,0,0,.1);
        border-radius: 50%;
        border-top-color: var(--primary-color, #1f77b4);
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Pagination controls */
    .pagination-controls {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 10px;
        margin: 20px 0;
        padding: 10px;
        background-color: var(--background-color, #ffffff);
        border-radius: 8px;
        border: 1px solid var(--border-color, #e0e0e0);
    }
    
    .pagination-info {
        font-size: 14px;
        color: var(--text-color-secondary, #666);
        margin: 0 15px;
    }
    
    /* Performance dashboard */
    .performance-metric {
        text-align: center;
        padding: 10px;
        background-color: var(--secondary-bg, #f8f9fa);
        border-radius: 6px;
        border: 1px solid var(--border-color, #e0e0e0);
    }
    
    .performance-metric .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: var(--primary-color, #1f77b4);
    }
    
    .performance-metric .metric-label {
        font-size: 12px;
        color: var(--text-color-secondary, #666);
        margin-top: 5px;
    }
    
    /* Optimized message rendering */
    .message-container {
        contain: layout style paint;
    }
    
    /* Responsive improvements */
    @media (max-width: 768px) {
        .pagination-controls {
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .pagination-info {
            margin: 5px 0;
            font-size: 12px;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)