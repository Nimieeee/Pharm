"""
Unlimited History Performance Optimizer
Implements efficient loading strategies, virtual scrolling, and database optimizations
for displaying unlimited conversation history without performance degradation.
"""

import streamlit as st
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, Generator
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

from message_store import Message, MessageStore
from performance_optimizer import performance_optimizer, LoadingStateManager
from supabase import Client

logger = logging.getLogger(__name__)

@dataclass
class VirtualScrollConfig:
    """Configuration for virtual scrolling"""
    viewport_height: int = 600  # Height of visible area in pixels
    item_height: int = 120      # Estimated height per message in pixels
    buffer_size: int = 10       # Number of items to render outside viewport
    chunk_size: int = 50        # Number of messages to load per chunk

@dataclass
class MessageChunk:
    """Chunk of messages for efficient loading"""
    messages: List[Message]
    start_index: int
    end_index: int
    total_count: int
    is_cached: bool = False
    load_time: float = 0.0

class UnlimitedHistoryOptimizer:
    """Optimizer for unlimited conversation history display"""
    
    def __init__(self, supabase_client: Client, message_store: MessageStore):
        """
        Initialize unlimited history optimizer
        
        Args:
            supabase_client: Supabase client for database operations
            message_store: Message store instance
        """
        self.client = supabase_client
        self.message_store = message_store
        self.virtual_scroll_config = VirtualScrollConfig()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for unlimited history"""
        if 'unlimited_history_cache' not in st.session_state:
            st.session_state.unlimited_history_cache = {}
        if 'virtual_scroll_state' not in st.session_state:
            st.session_state.virtual_scroll_state = {
                'scroll_position': 0,
                'visible_range': (0, 50),
                'loaded_chunks': {},
                'total_messages': 0
            }
        if 'lazy_loading_state' not in st.session_state:
            st.session_state.lazy_loading_state = {
                'is_loading': False,
                'loaded_ranges': [],
                'pending_ranges': []
            }
    
    def get_unlimited_messages_optimized(self, user_id: str, 
                                       conversation_id: Optional[str] = None) -> List[Message]:
        """
        Get unlimited messages with performance optimizations
        
        Args:
            user_id: User's unique identifier
            conversation_id: Optional conversation ID for filtering
            
        Returns:
            List of all messages with optimizations applied
        """
        cache_key = f"unlimited_messages:{user_id}:{conversation_id or 'all'}"
        
        # Check cache first
        cached_messages = performance_optimizer.get_cached_user_data(user_id, f"unlimited_{conversation_id or 'all'}")
        if cached_messages is not None:
            logger.info(f"Cache hit for unlimited messages: {len(cached_messages)} messages")
            return cached_messages
        
        start_time = time.time()
        
        try:
            # Use optimized database function for better performance
            if conversation_id:
                messages = self._get_conversation_messages_optimized(user_id, conversation_id)
            else:
                messages = self._get_all_user_messages_optimized(user_id)
            
            # Cache with shorter TTL for unlimited messages to ensure freshness
            performance_optimizer.set_cached_user_data(
                user_id, 
                f"unlimited_{conversation_id or 'all'}", 
                messages, 
                ttl=30  # 30 seconds cache for unlimited messages
            )
            
            load_time = time.time() - start_time
            logger.info(f"Loaded {len(messages)} unlimited messages in {load_time:.2f}s")
            
            return messages
            
        except Exception as e:
            logger.error(f"Error loading unlimited messages: {e}")
            return []
    
    def _get_all_user_messages_optimized(self, user_id: str) -> List[Message]:
        """Get all user messages using optimized database query"""
        try:
            # Use database function for better performance
            result = self.client.rpc('get_all_user_messages_unlimited', {
                'user_id': user_id
            }).execute()
            
            if not result.data:
                # Fallback to direct query if function doesn't exist
                result = self.client.table('messages').select('*').eq(
                    'user_id', user_id
                ).order('created_at', desc=False).execute()
            
            messages = []
            for data in result.data or []:
                messages.append(Message(
                    id=data['id'],
                    user_id=data['user_id'],
                    role=data['role'],
                    content=data['content'],
                    model_used=data.get('model_used'),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    metadata=data.get('metadata', {})
                ))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error in optimized message query: {e}")
            # Fallback to standard method
            return self.message_store.get_conversation_history(user_id, limit=10000)
    
    def _get_conversation_messages_optimized(self, user_id: str, conversation_id: str) -> List[Message]:
        """Get conversation messages using optimized database query"""
        try:
            # Use database function for better performance
            result = self.client.rpc('get_conversation_messages_unlimited', {
                'user_id': user_id,
                'conversation_id': conversation_id
            }).execute()
            
            if not result.data:
                # Fallback to direct query if function doesn't exist
                result = self.client.table('messages').select('*').eq(
                    'user_id', user_id
                ).eq('conversation_id', conversation_id).order('created_at', desc=False).execute()
            
            messages = []
            for data in result.data or []:
                messages.append(Message(
                    id=data['id'],
                    user_id=data['user_id'],
                    role=data['role'],
                    content=data['content'],
                    model_used=data.get('model_used'),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    metadata=data.get('metadata', {})
                ))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error in optimized conversation query: {e}")
            # Fallback to standard method
            return self.message_store.get_conversation_messages(user_id, conversation_id)
    
    def render_virtual_scrolled_messages(self, messages: List[Message], 
                                       container_height: int = 600) -> None:
        """
        Render messages with virtual scrolling for performance
        
        Args:
            messages: List of all messages
            container_height: Height of the scrollable container
        """
        total_messages = len(messages)
        
        if total_messages == 0:
            st.info("No messages to display")
            return
        
        # Calculate virtual scrolling parameters
        item_height = self.virtual_scroll_config.item_height
        viewport_items = container_height // item_height
        buffer_size = self.virtual_scroll_config.buffer_size
        
        # Get current scroll position from session state
        scroll_state = st.session_state.virtual_scroll_state
        current_position = scroll_state.get('scroll_position', 0)
        
        # Calculate visible range with buffer
        start_index = max(0, current_position - buffer_size)
        end_index = min(total_messages, current_position + viewport_items + buffer_size)
        
        # Update session state
        scroll_state['visible_range'] = (start_index, end_index)
        scroll_state['total_messages'] = total_messages
        
        # Create virtual scrolling container
        st.markdown(f"""
        <div class="virtual-scroll-container" style="height: {container_height}px; overflow-y: auto;">
            <div class="virtual-scroll-spacer-top" style="height: {start_index * item_height}px;"></div>
        """, unsafe_allow_html=True)
        
        # Render only visible messages
        visible_messages = messages[start_index:end_index]
        
        with st.container():
            for i, message in enumerate(visible_messages):
                actual_index = start_index + i
                self._render_virtual_message(message, actual_index)
        
        # Bottom spacer
        remaining_height = (total_messages - end_index) * item_height
        st.markdown(f"""
            <div class="virtual-scroll-spacer-bottom" style="height: {remaining_height}px;"></div>
        </div>
        """, unsafe_allow_html=True)
        
        # Add scroll position tracking
        self._inject_scroll_tracking_script()
    
    def render_lazy_loaded_messages(self, user_id: str, 
                                  conversation_id: Optional[str] = None,
                                  initial_load_count: int = 50) -> None:
        """
        Render messages with lazy loading for better performance
        
        Args:
            user_id: User's unique identifier
            conversation_id: Optional conversation ID
            initial_load_count: Number of messages to load initially
        """
        lazy_state = st.session_state.lazy_loading_state
        
        # Get total message count first
        total_count = self._get_message_count_optimized(user_id, conversation_id)
        
        if total_count == 0:
            st.info("No messages to display")
            return
        
        # Initialize loaded ranges if empty
        if not lazy_state['loaded_ranges']:
            lazy_state['loaded_ranges'] = [(0, min(initial_load_count, total_count))]
        
        # Load messages for all loaded ranges
        all_loaded_messages = []
        for start, end in lazy_state['loaded_ranges']:
            chunk_messages = self._load_message_chunk(user_id, conversation_id, start, end - start)
            all_loaded_messages.extend(chunk_messages)
        
        # Sort messages chronologically
        all_loaded_messages.sort(key=lambda m: m.created_at)
        
        # Render loaded messages
        st.markdown("#### 📜 Conversation History (Lazy Loaded)")
        st.caption(f"Loaded {len(all_loaded_messages)} of {total_count} messages")
        
        # Create scrollable container
        st.markdown('<div class="lazy-load-container">', unsafe_allow_html=True)
        
        for message in all_loaded_messages:
            self._render_message_bubble(message)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Load more button if there are more messages
        loaded_count = sum(end - start for start, end in lazy_state['loaded_ranges'])
        if loaded_count < total_count:
            if st.button(f"📥 Load More Messages ({total_count - loaded_count} remaining)", 
                        key="load_more_messages"):
                self._load_next_chunk(user_id, conversation_id, total_count)
                st.rerun()
    
    def render_chunked_unlimited_history(self, user_id: str, 
                                       conversation_id: Optional[str] = None) -> None:
        """
        Render unlimited history using chunked loading strategy
        
        Args:
            user_id: User's unique identifier
            conversation_id: Optional conversation ID
        """
        # Get total message count
        total_count = self._get_message_count_optimized(user_id, conversation_id)
        
        if total_count == 0:
            st.info("No messages in this conversation yet")
            return
        
        # Show unlimited history header
        st.markdown("#### 📜 Complete Conversation History")
        st.caption(f"Loading all {total_count} messages with optimized chunking")
        
        # Create progress indicator
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Load messages in chunks
        chunk_size = self.virtual_scroll_config.chunk_size
        all_messages = []
        
        for chunk_start in range(0, total_count, chunk_size):
            chunk_end = min(chunk_start + chunk_size, total_count)
            progress = chunk_end / total_count
            
            status_text.text(f"Loading messages {chunk_start + 1}-{chunk_end} of {total_count}...")
            progress_bar.progress(progress)
            
            # Load chunk
            chunk_messages = self._load_message_chunk(user_id, conversation_id, chunk_start, chunk_size)
            all_messages.extend(chunk_messages)
            
            # Small delay to prevent UI blocking
            time.sleep(0.01)
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Sort messages chronologically
        all_messages.sort(key=lambda m: m.created_at)
        
        # Render all messages
        st.success(f"✅ Loaded all {len(all_messages)} messages successfully!")
        
        # Create optimized container for unlimited scrolling
        st.markdown('<div class="unlimited-history-container">', unsafe_allow_html=True)
        
        for message in all_messages:
            self._render_message_bubble(message)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Auto-scroll to bottom
        self._inject_auto_scroll_script()
    
    def _get_message_count_optimized(self, user_id: str, conversation_id: Optional[str] = None) -> int:
        """Get message count using optimized query"""
        try:
            if conversation_id:
                result = self.client.table('messages').select(
                    'id', count='exact'
                ).eq('user_id', user_id).eq('conversation_id', conversation_id).execute()
            else:
                result = self.client.table('messages').select(
                    'id', count='exact'
                ).eq('user_id', user_id).execute()
            
            return result.count or 0
            
        except Exception as e:
            logger.error(f"Error getting message count: {e}")
            return 0
    
    def _load_message_chunk(self, user_id: str, conversation_id: Optional[str], 
                          offset: int, limit: int) -> List[Message]:
        """Load a chunk of messages with caching"""
        cache_key = f"chunk:{user_id}:{conversation_id or 'all'}:{offset}:{limit}"
        
        # Check cache first
        cached_chunk = performance_optimizer.cache.get(cache_key)
        if cached_chunk:
            return cached_chunk
        
        try:
            query = self.client.table('messages').select('*').eq('user_id', user_id)
            
            if conversation_id:
                query = query.eq('conversation_id', conversation_id)
            
            result = query.order('created_at', desc=False).range(offset, offset + limit - 1).execute()
            
            messages = []
            for data in result.data or []:
                messages.append(Message(
                    id=data['id'],
                    user_id=data['user_id'],
                    role=data['role'],
                    content=data['content'],
                    model_used=data.get('model_used'),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    metadata=data.get('metadata', {})
                ))
            
            # Cache chunk for 60 seconds
            performance_optimizer.cache.set(cache_key, messages, ttl=60)
            
            return messages
            
        except Exception as e:
            logger.error(f"Error loading message chunk: {e}")
            return []
    
    def _load_next_chunk(self, user_id: str, conversation_id: Optional[str], total_count: int) -> None:
        """Load the next chunk of messages"""
        lazy_state = st.session_state.lazy_loading_state
        
        # Calculate next range to load
        loaded_count = sum(end - start for start, end in lazy_state['loaded_ranges'])
        chunk_size = self.virtual_scroll_config.chunk_size
        
        next_start = loaded_count
        next_end = min(next_start + chunk_size, total_count)
        
        if next_start < total_count:
            lazy_state['loaded_ranges'].append((next_start, next_end))
    
    def _render_virtual_message(self, message: Message, index: int) -> None:
        """Render a single message in virtual scrolling context"""
        # Add index for debugging
        message_id = f"msg-{index}-{message.id}"
        
        # Use optimized message rendering
        self._render_message_bubble(message, virtual_index=index)
    
    def _render_message_bubble(self, message: Message, virtual_index: Optional[int] = None) -> None:
        """Render optimized message bubble"""
        bubble_class = "user-message" if message.role == "user" else "ai-message"
        role_display = "You" if message.role == "user" else "AI Assistant"
        
        # Format timestamp
        time_str = message.created_at.strftime("%H:%M") if message.created_at else "Unknown"
        
        # Add model info for AI messages
        model_info = ""
        if message.role == "assistant" and message.model_used:
            model_display = "🚀 Fast" if "gemma" in message.model_used.lower() else "⭐ Premium"
            model_info = f" • {model_display}"
        
        # Format content with length optimization for virtual scrolling
        content = message.content
        if virtual_index is not None and len(content) > 500:
            # Truncate very long messages in virtual scrolling for performance
            content = content[:500] + "... [truncated]"
        
        # Escape HTML and format
        content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        content = content.replace('\n', '<br>')
        
        # Add virtual index for debugging
        debug_info = f" #{virtual_index}" if virtual_index is not None else ""
        
        message_html = f"""
        <div class="message-bubble {bubble_class} optimized" data-message-id="{message.id}">
            <div class="message-role">{role_display}{model_info} • {time_str}{debug_info}</div>
            <div class="message-content">{content}</div>
        </div>
        """
        
        st.markdown(message_html, unsafe_allow_html=True)
    
    def _inject_scroll_tracking_script(self) -> None:
        """Inject JavaScript for tracking scroll position in virtual scrolling"""
        script = """
        <script>
        function trackScrollPosition() {
            const container = document.querySelector('.virtual-scroll-container');
            if (container) {
                const scrollTop = container.scrollTop;
                const itemHeight = 120; // Should match VirtualScrollConfig.item_height
                const currentPosition = Math.floor(scrollTop / itemHeight);
                
                // Store scroll position (in a real app, you'd send this to Streamlit)
                console.log('Virtual scroll position:', currentPosition);
            }
        }
        
        // Attach scroll listener
        const container = document.querySelector('.virtual-scroll-container');
        if (container) {
            container.addEventListener('scroll', trackScrollPosition);
        }
        </script>
        """
        st.markdown(script, unsafe_allow_html=True)
    
    def _inject_auto_scroll_script(self) -> None:
        """Inject JavaScript for auto-scrolling to bottom"""
        script = """
        <script>
        function scrollToBottom() {
            const containers = [
                document.querySelector('.unlimited-history-container'),
                document.querySelector('.lazy-load-container'),
                document.querySelector('.virtual-scroll-container')
            ];
            
            for (const container of containers) {
                if (container) {
                    container.scrollTop = container.scrollHeight;
                    break;
                }
            }
        }
        
        // Scroll after content is rendered
        setTimeout(scrollToBottom, 100);
        </script>
        """
        st.markdown(script, unsafe_allow_html=True)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for unlimited history"""
        cache_stats = performance_optimizer.cache.get_stats()
        
        return {
            "cache_entries": cache_stats.get("total_entries", 0),
            "cache_hit_rate": cache_stats.get("hit_rate", 0),
            "memory_usage_mb": cache_stats.get("memory_usage_mb", 0),
            "virtual_scroll_config": {
                "viewport_height": self.virtual_scroll_config.viewport_height,
                "item_height": self.virtual_scroll_config.item_height,
                "buffer_size": self.virtual_scroll_config.buffer_size,
                "chunk_size": self.virtual_scroll_config.chunk_size
            },
            "session_state_size": len(st.session_state.get('unlimited_history_cache', {}))
        }
    
    def clear_unlimited_history_cache(self, user_id: Optional[str] = None) -> None:
        """Clear unlimited history cache"""
        if user_id:
            # Clear user-specific cache
            performance_optimizer.invalidate_user_cache(user_id)
            
            # Clear session state cache
            cache_keys_to_remove = [
                key for key in st.session_state.unlimited_history_cache.keys()
                if key.startswith(f"unlimited_messages:{user_id}")
            ]
            for key in cache_keys_to_remove:
                del st.session_state.unlimited_history_cache[key]
        else:
            # Clear all cache
            performance_optimizer.cache.clear()
            st.session_state.unlimited_history_cache = {}
        
        # Reset virtual scroll state
        st.session_state.virtual_scroll_state = {
            'scroll_position': 0,
            'visible_range': (0, 50),
            'loaded_chunks': {},
            'total_messages': 0
        }
        
        # Reset lazy loading state
        st.session_state.lazy_loading_state = {
            'is_loading': False,
            'loaded_ranges': [],
            'pending_ranges': []
        }

def inject_unlimited_history_css() -> None:
    """Inject CSS for unlimited history optimizations"""
    css = """
    <style>
    /* Unlimited History Performance Optimizations */
    .unlimited-history-container {
        max-height: 70vh;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 1rem;
        border: 1px solid var(--border-color, #4b5563);
        border-radius: 0.5rem;
        background-color: var(--background-color, #0e1117);
        scroll-behavior: smooth;
        /* Performance optimizations */
        contain: layout style paint;
        will-change: scroll-position;
        transform: translateZ(0);
        /* Enable hardware acceleration */
        -webkit-transform: translateZ(0);
        -webkit-backface-visibility: hidden;
        -webkit-perspective: 1000;
    }
    
    /* Virtual Scrolling Container */
    .virtual-scroll-container {
        position: relative;
        overflow-y: auto;
        overflow-x: hidden;
        border: 1px solid var(--border-color, #4b5563);
        border-radius: 0.5rem;
        background-color: var(--background-color, #0e1117);
        /* Performance optimizations for virtual scrolling */
        contain: strict;
        will-change: scroll-position;
        transform: translateZ(0);
    }
    
    .virtual-scroll-spacer-top,
    .virtual-scroll-spacer-bottom {
        width: 100%;
        pointer-events: none;
    }
    
    /* Lazy Loading Container */
    .lazy-load-container {
        max-height: 70vh;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 1rem;
        border: 1px solid var(--border-color, #4b5563);
        border-radius: 0.5rem;
        background-color: var(--background-color, #0e1117);
        scroll-behavior: smooth;
        /* Performance optimizations */
        contain: layout style paint;
        will-change: scroll-position;
        transform: translateZ(0);
    }
    
    /* Optimized Message Bubbles */
    .message-bubble.optimized {
        /* Performance optimizations for message rendering */
        contain: layout style paint;
        will-change: transform;
        transform: translateZ(0);
        backface-visibility: hidden;
        /* Reduce repaints */
        border-radius: 0.75rem;
        margin-bottom: 1rem;
        padding: 1rem;
        max-width: 85%;
        word-wrap: break-word;
        /* Optimize text rendering */
        text-rendering: optimizeSpeed;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    .message-bubble.optimized.user-message {
        background: linear-gradient(135deg, var(--primary-color, #4fc3f7) 0%, color-mix(in srgb, var(--primary-color, #4fc3f7) 85%, #000) 100%);
        color: white;
        margin-left: auto;
        margin-right: 0;
    }
    
    .message-bubble.optimized.ai-message {
        background: linear-gradient(135deg, var(--secondary-bg, #262730) 0%, color-mix(in srgb, var(--secondary-bg, #262730) 95%, white) 100%);
        color: var(--text-color, #ffffff);
        border: 1px solid var(--border-color, #4b5563);
        margin-left: 0;
        margin-right: auto;
    }
    
    .message-bubble.optimized .message-role {
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        opacity: 0.9;
        /* Optimize text rendering */
        text-rendering: optimizeSpeed;
    }
    
    .message-bubble.optimized .message-content {
        line-height: 1.5;
        /* Optimize text rendering */
        text-rendering: optimizeSpeed;
        word-break: break-word;
        overflow-wrap: break-word;
    }
    
    /* Custom Scrollbars for Performance */
    .unlimited-history-container::-webkit-scrollbar,
    .virtual-scroll-container::-webkit-scrollbar,
    .lazy-load-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .unlimited-history-container::-webkit-scrollbar-track,
    .virtual-scroll-container::-webkit-scrollbar-track,
    .lazy-load-container::-webkit-scrollbar-track {
        background: var(--secondary-bg, #262730);
        border-radius: 4px;
    }
    
    .unlimited-history-container::-webkit-scrollbar-thumb,
    .virtual-scroll-container::-webkit-scrollbar-thumb,
    .lazy-load-container::-webkit-scrollbar-thumb {
        background: var(--border-color, #4b5563);
        border-radius: 4px;
        transition: background 0.2s ease;
    }
    
    .unlimited-history-container::-webkit-scrollbar-thumb:hover,
    .virtual-scroll-container::-webkit-scrollbar-thumb:hover,
    .lazy-load-container::-webkit-scrollbar-thumb:hover {
        background: var(--primary-color, #4fc3f7);
    }
    
    /* Loading States */
    .loading-chunk {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        color: var(--text-color, #ffffff);
        opacity: 0.7;
    }
    
    .loading-chunk .spinner {
        width: 20px;
        height: 20px;
        border: 2px solid var(--border-color, #4b5563);
        border-top: 2px solid var(--primary-color, #4fc3f7);
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 0.5rem;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Performance Metrics Display */
    .performance-metrics {
        background: var(--secondary-bg, #262730);
        border: 1px solid var(--border-color, #4b5563);
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        font-family: monospace;
        font-size: 0.8rem;
        color: var(--text-color, #ffffff);
    }
    
    .performance-metrics .metric-item {
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.25rem;
    }
    
    .performance-metrics .metric-value {
        color: var(--primary-color, #4fc3f7);
        font-weight: bold;
    }
    
    /* Responsive Optimizations */
    @media (max-width: 768px) {
        .unlimited-history-container,
        .virtual-scroll-container,
        .lazy-load-container {
            max-height: 60vh;
            padding: 0.5rem;
        }
        
        .message-bubble.optimized {
            max-width: 95%;
            padding: 0.75rem;
            margin-bottom: 0.75rem;
        }
        
        .message-bubble.optimized .message-role {
            font-size: 0.75rem;
        }
        
        .message-bubble.optimized .message-content {
            font-size: 0.9rem;
            line-height: 1.4;
        }
    }
    
    @media (max-width: 480px) {
        .unlimited-history-container,
        .virtual-scroll-container,
        .lazy-load-container {
            max-height: 50vh;
            padding: 0.25rem;
        }
        
        .message-bubble.optimized {
            padding: 0.5rem;
            margin-bottom: 0.5rem;
        }
    }
    
    /* Accessibility Improvements */
    @media (prefers-reduced-motion: reduce) {
        .unlimited-history-container,
        .virtual-scroll-container,
        .lazy-load-container {
            scroll-behavior: auto;
        }
        
        .message-bubble.optimized {
            transition: none;
        }
        
        .loading-chunk .spinner {
            animation: none;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)