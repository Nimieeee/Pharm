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
import logging
from pathlib import Path

from message_store import Message
from message_store_optimized import MessagePage, OptimizedMessageStore
from theme_manager import ThemeManager
from performance_optimizer import performance_optimizer, PaginationHelper, LoadingStateManager
from chat_interface import ChatInterface, StreamingMessage

logger = logging.getLogger(__name__)

class OptimizedChatInterface(ChatInterface):
    """Enhanced chat interface with pagination, loading states, and performance optimizations"""
    
    def __init__(self, theme_manager: ThemeManager, message_store: Optional[OptimizedMessageStore] = None):
        super().__init__(theme_manager)
        self.message_store = message_store
        self._initialize_unlimited_history_state()
    
    def _initialize_unlimited_history_state(self):
        """Initialize unlimited history-related session state"""
        if 'loading_states' not in st.session_state:
            st.session_state.loading_states = {}
        if 'unlimited_history_loaded' not in st.session_state:
            st.session_state.unlimited_history_loaded = False
    
    def render_unlimited_chat_history(self, user_id: str) -> None:
        """
        Render unlimited chat history without pagination controls
        
        Args:
            user_id: User's unique identifier
        """
        if not self.message_store:
            st.error("Message store not available")
            return
        
        # Show loading state
        with LoadingStateManager.show_loading_spinner("Loading complete conversation history..."):
            # Get all messages without pagination limits
            all_messages = self.message_store.get_all_user_messages(user_id)
        
        # Show cache hit indicator for debugging
        if hasattr(all_messages, 'cache_hit') and all_messages.cache_hit:
            st.caption("📋 Loaded from cache")
        
        # Render messages
        if not all_messages and not st.session_state.show_typing_indicator:
            self._render_welcome_message()
        else:
            # Create scrollable container for unlimited messages
            self._render_unlimited_message_container(all_messages)
        
        # Always auto-scroll to bottom for unlimited history
        self._inject_auto_scroll_script()
    
    def render_unlimited_conversation_history(self, user_id: str, conversation_id: Optional[str] = None) -> None:
        """
        Render unlimited conversation history for a specific conversation with tabs support
        
        Args:
            user_id: User's unique identifier
            conversation_id: Optional conversation ID to filter messages
        """
        if not self.message_store:
            st.error("Message store not available")
            return
        
        # Show loading state
        with LoadingStateManager.show_loading_spinner("Loading complete conversation history..."):
            if conversation_id:
                # Get messages for specific conversation
                all_messages = self.message_store.get_conversation_messages(user_id, conversation_id)
            else:
                # Get all messages for user
                all_messages = self.message_store.get_all_user_messages(user_id)
        
        # Show cache hit indicator for debugging
        if hasattr(all_messages, 'cache_hit') and all_messages.cache_hit:
            st.caption("📋 Loaded from cache")
        
        # Render messages
        if not all_messages and not st.session_state.show_typing_indicator:
            self._render_welcome_message()
        else:
            # Create scrollable container for unlimited messages with conversation context
            self._render_unlimited_message_container_with_tabs(all_messages, conversation_id)
        
        # Always auto-scroll to bottom for unlimited history
        self._inject_auto_scroll_script()
    
    def _render_unlimited_message_container(self, messages: List[Message]) -> None:
        """
        Render unlimited message container with efficient scrolling
        
        Args:
            messages: List of all messages to display
        """
        # Render header
        self._render_unlimited_history_header()
        
        # Show message count
        if messages:
            st.caption(f"📊 Displaying {len(messages)} messages")
        
        # Create container with custom styling for unlimited scrolling
        st.markdown(
            '<div class="unlimited-chat-container" id="unlimited-chat-container">',
            unsafe_allow_html=True
        )
        
        # Use container for better performance with large message lists
        chat_container = st.container()
        
        with chat_container:
            # Render messages in chronological order (oldest first)
            for message in messages:
                self._render_message_bubble(message)
            
            # Render streaming message if active
            if st.session_state.streaming_message:
                self._render_streaming_message(st.session_state.streaming_message)
            
            # Render typing indicator if active
            elif st.session_state.show_typing_indicator:
                self._render_typing_indicator()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_unlimited_message_container_with_tabs(self, messages: List[Message], conversation_id: Optional[str] = None) -> None:
        """
        Render unlimited message container with conversation tabs support
        
        Args:
            messages: List of all messages to display
            conversation_id: Optional conversation ID for context
        """
        # Render header with conversation context
        self._render_unlimited_history_header_with_tabs(len(messages), conversation_id)
        
        # Show message count and conversation info
        if messages:
            st.caption(f"📊 Displaying {len(messages)} messages")
            if conversation_id:
                st.caption(f"🔗 Conversation ID: {conversation_id}")
        
        # Create container with custom styling for unlimited scrolling
        st.markdown(
            '<div class="unlimited-chat-container conversation-tab-content" id="unlimited-chat-container">',
            unsafe_allow_html=True
        )
        
        # Use container for better performance with large message lists
        chat_container = st.container()
        
        with chat_container:
            # Render messages in chronological order (oldest first)
            for message in messages:
                self._render_message_bubble(message)
            
            # Render streaming message if active
            if st.session_state.streaming_message:
                self._render_streaming_message(st.session_state.streaming_message)
            
            # Render typing indicator if active
            elif st.session_state.show_typing_indicator:
                self._render_typing_indicator()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
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
    
    def _render_unlimited_history_header(self) -> None:
        """Render header for unlimited conversation history"""
        st.markdown("#### 📜 Complete Conversation History")
        st.caption("Showing all messages without pagination limits")
    
    def _render_unlimited_history_header_with_tabs(self, message_count: int, conversation_id: Optional[str] = None) -> None:
        """Render header for unlimited conversation history with tabs context"""
        if conversation_id:
            st.markdown("#### 📜 Complete Conversation History")
            st.caption("Showing all messages in this conversation without pagination limits")
        else:
            st.markdown("#### 📜 Complete Conversation History")
            st.caption("Showing all messages without pagination limits")
        
        if message_count > 0:
            st.caption(f"Total messages: {message_count}")
        else:
            st.caption("No messages yet - start a conversation!")
    
    def _render_enhanced_statistics(self, stats: Dict[str, Any]) -> None:
        """Render enhanced conversation statistics for unlimited history"""
        total_messages = stats.get('total_messages', 0)
        
        if total_messages > 0:
            st.markdown("**📊 Conversation Statistics:**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Messages", total_messages)
            
            with col2:
                recent_messages = stats.get('recent_messages', 0)
                st.metric("Recent (24h)", recent_messages)
            
            # Model usage breakdown
            models_used = stats.get('models_used', {})
            if models_used:
                st.markdown("**Model Usage:**")
                for model, count in models_used.items():
                    if model and model != 'unknown':
                        model_display = "🚀 Fast" if "gemma" in model.lower() else "⭐ Premium"
                        st.write(f"• {model_display}: {count} responses")
        else:
            st.info("No conversation history yet")
    
    def _handle_refresh_action(self, user_id: str) -> None:
        """Handle refresh action - clear caches and reload unlimited history"""
        # Clear user-specific caches
        performance_optimizer.invalidate_user_cache(user_id)
        
        # Reset unlimited history state
        st.session_state.unlimited_history_loaded = False
        
        # Clear any loading states
        st.session_state.loading_states = {}
        
        st.success("🔄 Unlimited conversation history refreshed and cache cleared!")
    
    def render_unlimited_history_settings(self) -> None:
        """Render settings for unlimited history display"""
        st.markdown("#### ⚙️ Display Settings")
        
        # Show unlimited history status
        st.info("📜 **Unlimited History Mode**\nShowing complete conversation history without pagination")
        
        # Option to refresh cache
        if st.button("🔄 Refresh History", key="refresh_unlimited_history"):
            # Clear cache to force reload
            user_id = st.session_state.get('user_id')
            if user_id and self.message_store:
                performance_optimizer.invalidate_user_cache(user_id)
                st.success("History cache refreshed!")
                st.rerun()
    
    def render_header_model_toggle_optimized(self, current_model: str, on_change_callback=None) -> str:
        """
        Render optimized model toggle switch for chat header with performance tracking
        
        Args:
            current_model: Currently selected model
            on_change_callback: Callback function when model changes
            
        Returns:
            Selected model identifier
        """
        # Track performance of model toggle rendering
        start_time = time.time()
        
        try:
            # Use the parent class method
            selected_model = self.render_header_model_toggle(current_model, on_change_callback)
            
            # Record performance metric
            performance_optimizer._record_metric(
                operation_name="render_header_model_toggle",
                start_time=start_time,
                cache_hit=False
            )
            
            return selected_model
            
        except Exception as e:
            logger.error(f"Error rendering header model toggle: {e}")
            return current_model

def inject_optimized_chat_css() -> None:
    """Inject optimized CSS for enhanced chat interface with dark theme and model toggle"""
    css = """
    <style>
    /* Performance optimizations with dark theme */
    .message-bubble {
        will-change: transform;
        transform: translateZ(0);
        contain: layout style paint;
        backface-visibility: hidden;
    }
    
    /* Loading states with dark theme */
    .loading-overlay {
        position: relative;
        opacity: 0.6;
        pointer-events: none;
    }
    
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255,255,255,.1);
        border-radius: 50%;
        border-top-color: var(--primary-color, #4fc3f7);
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Performance dashboard with dark theme */
    .performance-metric {
        text-align: center;
        padding: 10px;
        background-color: var(--secondary-bg, #262730);
        border-radius: 6px;
        border: 1px solid var(--border-color, #4b5563);
        color: var(--text-color, #ffffff);
    }
    
    .performance-metric .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: var(--primary-color, #4fc3f7);
    }
    
    .performance-metric .metric-label {
        font-size: 12px;
        color: var(--text-color, #ffffff);
        margin-top: 5px;
        opacity: 0.8;
    }
    
    /* Optimized message rendering */
    .message-container {
        contain: layout style paint;
    }
    
    /* Unlimited chat container for efficient scrolling with dark theme */
    .unlimited-chat-container {
        max-height: 70vh;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 1rem;
        border: 1px solid var(--border-color, #4b5563);
        border-radius: 0.5rem;
        background-color: var(--background-color, #0e1117);
        scroll-behavior: smooth;
        /* Performance optimizations for large message lists */
        contain: layout style paint;
        will-change: scroll-position;
        transform: translateZ(0);
    }
    
    /* Optimize message rendering for unlimited scrolling */
    .unlimited-chat-container .message-bubble {
        contain: layout style paint;
        transform: translateZ(0);
        backface-visibility: hidden;
    }
    
    /* Custom scrollbar for unlimited chat with dark theme */
    .unlimited-chat-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .unlimited-chat-container::-webkit-scrollbar-track {
        background: var(--secondary-bg, #262730);
        border-radius: 4px;
    }
    
    .unlimited-chat-container::-webkit-scrollbar-thumb {
        background: var(--border-color, #4b5563);
        border-radius: 4px;
    }
    
    .unlimited-chat-container::-webkit-scrollbar-thumb:hover {
        background: var(--primary-color, #4fc3f7);
    }
    
    /* Model Toggle Switch Styles for Optimized Interface */
    .model-toggle-container {
        background: linear-gradient(135deg, var(--secondary-bg, #262730), color-mix(in srgb, var(--secondary-bg, #262730) 95%, white));
        border: 1px solid var(--border-color, #4b5563);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px var(--shadow-color, rgba(0, 0, 0, 0.4));
        text-align: center;
    }
    
    .model-toggle-header h4 {
        color: var(--text-color, #ffffff);
        margin: 0 0 1rem 0;
        font-weight: 600;
    }
    
    .model-toggle-labels {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 1rem;
        font-weight: 500;
        margin: 1rem 0;
    }
    
    .model-toggle-labels.compact {
        gap: 0.5rem;
        margin: 0.5rem 0;
    }
    
    .toggle-label {
        color: var(--text-color, #ffffff);
        transition: all 0.3s ease;
        font-size: 0.9rem;
        min-width: 80px;
        text-align: center;
        opacity: 0.7;
    }
    
    .toggle-label.active {
        color: var(--primary-color, #4fc3f7);
        font-weight: 600;
        transform: scale(1.05);
        opacity: 1;
    }
    
    .toggle-switch-wrapper {
        display: flex;
        align-items: center;
    }
    
    .toggle-switch {
        position: relative;
        display: inline-block;
        width: 60px;
        height: 30px;
        cursor: pointer;
    }
    
    .toggle-switch.compact {
        width: 45px;
        height: 24px;
    }
    
    .toggle-switch input {
        opacity: 0;
        width: 0;
        height: 0;
    }
    
    .toggle-slider {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, #6c757d, #495057);
        border-radius: 30px;
        transition: all 0.3s ease;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .toggle-slider:before {
        position: absolute;
        content: "";
        height: 24px;
        width: 24px;
        left: 3px;
        bottom: 3px;
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        border-radius: 50%;
        transition: all 0.3s ease;
        box-shadow: 0 2px 6px rgba(0,0,0,0.4);
    }
    
    .toggle-switch.compact .toggle-slider:before {
        height: 18px;
        width: 18px;
        left: 3px;
        bottom: 3px;
    }
    
    .toggle-switch input:checked + .toggle-slider {
        background: linear-gradient(135deg, var(--primary-color, #4fc3f7), color-mix(in srgb, var(--primary-color, #4fc3f7) 80%, #000));
    }
    
    .toggle-switch input:checked + .toggle-slider:before {
        transform: translateX(30px);
        background: linear-gradient(135deg, #ffffff, #f0f8ff);
    }
    
    .toggle-switch.compact input:checked + .toggle-slider:before {
        transform: translateX(21px);
    }
    
    .toggle-switch:hover .toggle-slider {
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.3), 0 0 8px rgba(79, 195, 247, 0.3);
    }
    
    .model-description {
        color: var(--text-color, #ffffff);
        font-size: 0.85rem;
        text-align: center;
        font-style: italic;
        margin-top: 0.5rem;
        opacity: 0.8;
    }
    
    /* Header Model Toggle */
    .header-model-toggle {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.25rem;
        padding: 0.5rem;
        background: var(--secondary-bg, #262730);
        border: 1px solid var(--border-color, #4b5563);
        border-radius: 0.5rem;
    }
    
    .model-status-text {
        font-size: 0.75rem;
        color: var(--text-color, #ffffff);
        font-weight: 500;
        opacity: 0.9;
    }
    
    /* Conversation tabs integration with dark theme */
    .conversation-tab-content {
        background-color: var(--background-color, #0e1117);
        border-radius: 0.5rem;
        padding: 1rem;
        margin-top: 1rem;
        border: 1px solid var(--border-color, #4b5563);
    }
    
    /* Unlimited history status indicator */
    .unlimited-history-status {
        background: linear-gradient(135deg, var(--primary-color, #4fc3f7) 20%, transparent);
        border: 1px solid var(--primary-color, #4fc3f7);
        border-radius: 0.5rem;
        padding: 0.75rem;
        margin: 1rem 0;
        color: var(--text-color, #ffffff);
        text-align: center;
    }
    
    /* Responsive improvements with dark theme */
    @media (max-width: 768px) {
        .unlimited-chat-container {
            max-height: 60vh;
            padding: 0.5rem;
        }
        
        .model-toggle-container {
            padding: 1rem;
            margin: 0.75rem 0;
        }
        
        .model-toggle-labels {
            gap: 0.75rem;
        }
        
        .toggle-label {
            font-size: 0.8rem;
            min-width: 60px;
        }
        
        .toggle-switch {
            width: 50px;
            height: 26px;
        }
        
        .toggle-slider:before {
            height: 20px;
            width: 20px;
            left: 3px;
            bottom: 3px;
        }
        
        .toggle-switch input:checked + .toggle-slider:before {
            transform: translateX(24px);
        }
    }
    
    @media (max-width: 480px) {
        .unlimited-chat-container {
            max-height: 50vh;
            padding: 0.25rem;
        }
        
        .model-toggle-container {
            padding: 0.75rem;
        }
        
        .header-model-toggle {
            padding: 0.25rem;
        }
        
        .model-status-text {
            font-size: 0.7rem;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)