"""
Enhanced Chat Interface for Pharmacology Chat Application
Implements comprehensive chat interface with conversation management, streaming, and file attachments.
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
from theme_manager import ThemeManager


@dataclass
class StreamingMessage:
    """Represents a message being streamed in real-time"""
    content: str = ""
    is_complete: bool = False
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ChatInterface:
    """Enhanced chat interface with streaming, file attachments, and conversation management"""
    
    def __init__(self, theme_manager: ThemeManager):
        self.theme_manager = theme_manager
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for chat interface"""
        if 'streaming_message' not in st.session_state:
            st.session_state.streaming_message = None
        if 'show_typing_indicator' not in st.session_state:
            st.session_state.show_typing_indicator = False
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = []
        if 'chat_input_key' not in st.session_state:
            st.session_state.chat_input_key = 0
    
    def render_chat_container(self) -> None:
        """Render the main chat container with proper styling"""
        st.markdown(
            '<div class="chat-container" id="chat-container">',
            unsafe_allow_html=True
        )
    
    def render_chat_history(self, messages: List[Message]) -> None:
        """
        Render the complete chat history with enhanced message display
        
        Args:
            messages: List of Message objects to display
        """
        if not messages and not st.session_state.show_typing_indicator:
            self._render_welcome_message()
            return
        
        # Create a container for chat messages
        chat_container = st.container()
        
        with chat_container:
            # Render historical messages
            for message in messages:
                self._render_message_bubble(message)
            
            # Render streaming message if active
            if st.session_state.streaming_message:
                self._render_streaming_message(st.session_state.streaming_message)
            
            # Render typing indicator if active
            elif st.session_state.show_typing_indicator:
                self._render_typing_indicator()
        
        # Auto-scroll to bottom (JavaScript injection)
        self._inject_auto_scroll_script()
    
    def render_message_input_with_attachments(self, 
                                            placeholder: str = "Ask about pharmacology...",
                                            enable_attachments: bool = True) -> Dict[str, Any]:
        """
        Render enhanced message input with file attachment support
        
        Args:
            placeholder: Placeholder text for input
            enable_attachments: Whether to enable file attachments
            
        Returns:
            Dictionary with 'message' and 'files' if submitted, empty dict otherwise
        """
        st.markdown("---")
        
        # File attachment section
        uploaded_files = []
        if enable_attachments:
            uploaded_files = self._render_file_attachment_section()
        
        # Message input section
        with st.container():
            col1, col2 = st.columns([5, 1])
            
            with col1:
                # Use a unique key that changes to clear input after sending
                user_input = st.text_input(
                    "Message",
                    placeholder=placeholder,
                    key=f"message_input_{st.session_state.chat_input_key}",
                    label_visibility="collapsed"
                )
            
            with col2:
                send_button = st.button(
                    "Send", 
                    key=f"send_button_{st.session_state.chat_input_key}",
                    use_container_width=True,
                    disabled=st.session_state.show_typing_indicator
                )
            
            # Handle send action
            if send_button and (user_input.strip() or uploaded_files):
                # Increment key to clear input
                st.session_state.chat_input_key += 1
                
                return {
                    'message': user_input.strip() if user_input else "",
                    'files': uploaded_files
                }
        
        return {}
    
    def render_conversation_controls(self, user_id: str, chat_manager) -> Dict[str, bool]:
        """
        Render conversation management controls
        
        Args:
            user_id: Current user ID
            chat_manager: ChatManager instance
            
        Returns:
            Dictionary of control actions triggered
        """
        st.markdown("### 💬 Conversation Controls")
        
        # Get conversation stats
        if chat_manager:
            stats = chat_manager.get_user_message_stats(user_id)
            total_messages = stats.get('total_messages', 0)
            
            st.write(f"**Messages in conversation:** {total_messages}")
        
        controls = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            controls['clear'] = st.button(
                "🗑️ Clear Chat",
                key="clear_conversation",
                use_container_width=True,
                help="Delete all messages in this conversation"
            )
        
        with col2:
            controls['export'] = st.button(
                "📥 Export",
                key="export_conversation", 
                use_container_width=True,
                help="Export conversation history"
            )
        
        # Confirmation dialog for clear action
        if controls['clear']:
            controls['clear_confirmed'] = self._render_clear_confirmation_dialog()
        else:
            controls['clear_confirmed'] = False
        
        return controls
    
    def start_streaming_response(self) -> None:
        """Start streaming response mode with typing indicator"""
        st.session_state.show_typing_indicator = True
        st.session_state.streaming_message = StreamingMessage()
    
    def update_streaming_message(self, chunk: str) -> None:
        """
        Update the streaming message with new content
        
        Args:
            chunk: New content chunk to append
        """
        if st.session_state.streaming_message:
            st.session_state.streaming_message.content += chunk
    
    def complete_streaming_message(self) -> str:
        """
        Complete the streaming message and return final content
        
        Returns:
            Complete message content
        """
        st.session_state.show_typing_indicator = False
        
        if st.session_state.streaming_message:
            final_content = st.session_state.streaming_message.content
            st.session_state.streaming_message = None
            return final_content
        
        return ""
    
    def render_model_selector(self, current_model: str, on_change_callback=None) -> str:
        """
        Render model selection interface
        
        Args:
            current_model: Currently selected model
            on_change_callback: Callback function when model changes
            
        Returns:
            Selected model identifier
        """
        st.markdown("### 🤖 AI Model Selection")
        
        model_options = {
            "🚀 Fast Mode (Gemma2-9B)": "fast",
            "⭐ Premium Mode (Qwen3-32B)": "premium"
        }
        
        # Find current selection
        current_display = next(
            (k for k, v in model_options.items() if v == current_model),
            list(model_options.keys())[0]
        )
        
        selected_display = st.radio(
            "Choose AI Model:",
            options=list(model_options.keys()),
            index=list(model_options.keys()).index(current_display),
            key="model_selector"
        )
        
        selected_model = model_options[selected_display]
        
        # Show model descriptions
        if selected_model == "fast":
            st.caption("⚡ Faster responses, good for quick questions")
        else:
            st.caption("🎯 Higher quality responses, better for complex topics")
        
        # Call callback if model changed
        if on_change_callback and selected_model != current_model:
            on_change_callback(selected_model)
        
        return selected_model
    
    def render_chat_statistics(self, stats: Dict[str, Any]) -> None:
        """
        Render chat statistics and information
        
        Args:
            stats: Dictionary containing chat statistics
        """
        st.markdown("### 📊 Chat Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Messages", stats.get('total_messages', 0))
        
        with col2:
            st.metric("Recent Messages", stats.get('recent_messages', 0))
        
        # Additional stats if available
        if 'models_used' in stats:
            st.markdown("**Models Used:**")
            for model, count in stats['models_used'].items():
                st.write(f"• {model}: {count} messages")
    
    def export_conversation(self, messages: List[Message], format: str = "txt") -> bytes:
        """
        Export conversation history in specified format
        
        Args:
            messages: List of messages to export
            format: Export format ('txt', 'json', 'csv')
            
        Returns:
            Exported data as bytes
        """
        if format == "txt":
            return self._export_as_text(messages)
        elif format == "json":
            return self._export_as_json(messages)
        elif format == "csv":
            return self._export_as_csv(messages)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _render_message_bubble(self, message: Message) -> None:
        """Render a single message bubble with enhanced styling"""
        bubble_class = "user-message" if message.role == "user" else "ai-message"
        role_display = "You" if message.role == "user" else "AI Assistant"
        
        # Format timestamp
        if hasattr(message, 'created_at') and message.created_at:
            time_str = message.created_at.strftime("%H:%M")
        else:
            time_str = datetime.now().strftime("%H:%M")
        
        # Add model info for AI messages
        model_info = ""
        if message.role == "assistant" and hasattr(message, 'model_used') and message.model_used:
            model_display = "🚀 Fast" if "gemma" in message.model_used.lower() else "⭐ Premium"
            model_info = f" • {model_display}"
        
        # Format message content
        formatted_content = self._format_message_content(message.content)
        
        message_html = f"""
        <div class="message-bubble {bubble_class}" data-message-id="{getattr(message, 'id', '')}">
            <div class="message-role">{role_display}{model_info} • {time_str}</div>
            <div class="message-content">{formatted_content}</div>
        </div>
        """
        
        st.markdown(message_html, unsafe_allow_html=True)
    
    def _render_streaming_message(self, streaming_msg: StreamingMessage) -> None:
        """Render a message that's currently being streamed"""
        formatted_content = self._format_message_content(streaming_msg.content)
        
        # Add cursor for streaming effect
        cursor = "▌" if not streaming_msg.is_complete else ""
        
        message_html = f"""
        <div class="message-bubble ai-message streaming">
            <div class="message-role">AI Assistant • Responding...</div>
            <div class="message-content">{formatted_content}{cursor}</div>
        </div>
        """
        
        st.markdown(message_html, unsafe_allow_html=True)
    
    def _render_typing_indicator(self) -> None:
        """Render typing indicator for AI responses"""
        typing_html = """
        <div class="message-bubble ai-message typing">
            <div class="message-role">AI Assistant</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span style="margin-left: 10px; opacity: 0.7;">Thinking...</span>
            </div>
        </div>
        """
        st.markdown(typing_html, unsafe_allow_html=True)
    
    def _render_welcome_message(self) -> None:
        """Render welcome message when no chat history exists"""
        welcome_html = """
        <div class="message-bubble ai-message welcome">
            <div class="message-role">AI Assistant</div>
            <div class="message-content">
                <strong>🧬 Welcome to Pharmacology Chat!</strong><br><br>
                I'm here to help you with pharmacology questions. You can ask me about:
                <ul>
                    <li>💊 Drug mechanisms and interactions</li>
                    <li>⚗️ Pharmacokinetics and pharmacodynamics</li>
                    <li>🏥 Clinical applications and dosing</li>
                    <li>⚠️ Side effects and contraindications</li>
                    <li>📚 Upload documents for personalized assistance</li>
                </ul>
                What would you like to know?
            </div>
        </div>
        """
        st.markdown(welcome_html, unsafe_allow_html=True)
    
    def _render_file_attachment_section(self) -> List[Any]:
        """Render file attachment interface"""
        st.markdown("#### 📎 Attach Files (Optional)")
        
        uploaded_files = st.file_uploader(
            "Upload documents to enhance responses",
            accept_multiple_files=True,
            type=['pdf', 'docx', 'txt', 'md', 'csv'],
            key="file_uploader",
            help="Upload pharmacology documents, research papers, or notes"
        )
        
        if uploaded_files:
            st.markdown("**Attached files:**")
            for file in uploaded_files:
                file_size = len(file.getvalue()) / 1024  # KB
                st.write(f"• {file.name} ({file_size:.1f} KB)")
        
        return uploaded_files or []
    
    def _render_clear_confirmation_dialog(self) -> bool:
        """Render confirmation dialog for clearing conversation"""
        st.warning("⚠️ This will permanently delete all messages in this conversation.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            confirm = st.button("Yes, Clear All", key="confirm_clear", type="primary")
        
        with col2:
            cancel = st.button("Cancel", key="cancel_clear")
        
        if cancel:
            st.rerun()
        
        return confirm
    
    def _format_message_content(self, content: str) -> str:
        """Format message content with proper HTML escaping and markdown-like formatting"""
        import re
        
        # Escape HTML
        content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Convert markdown-like formatting
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
        
        # Convert line breaks
        content = content.replace('\n', '<br>')
        
        # Convert URLs to links
        url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+)'
        content = re.sub(url_pattern, r'<a href="\1" target="_blank">\1</a>', content)
        
        return content
    
    def _inject_auto_scroll_script(self) -> None:
        """Inject JavaScript for auto-scrolling to bottom of chat"""
        scroll_script = """
        <script>
        function scrollToBottom() {
            const chatContainer = document.getElementById('chat-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
        
        // Scroll after a short delay to ensure content is rendered
        setTimeout(scrollToBottom, 100);
        </script>
        """
        st.markdown(scroll_script, unsafe_allow_html=True)
    
    def _export_as_text(self, messages: List[Message]) -> bytes:
        """Export messages as plain text"""
        output = io.StringIO()
        output.write("Pharmacology Chat Conversation Export\n")
        output.write("=" * 50 + "\n\n")
        
        for message in messages:
            timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(message, 'created_at') else "Unknown"
            role = "You" if message.role == "user" else "AI Assistant"
            
            output.write(f"[{timestamp}] {role}:\n")
            output.write(f"{message.content}\n\n")
        
        return output.getvalue().encode('utf-8')
    
    def _export_as_json(self, messages: List[Message]) -> bytes:
        """Export messages as JSON"""
        import json
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_messages": len(messages),
            "messages": []
        }
        
        for message in messages:
            msg_data = {
                "id": getattr(message, 'id', ''),
                "role": message.role,
                "content": message.content,
                "timestamp": message.created_at.isoformat() if hasattr(message, 'created_at') else None,
                "model_used": getattr(message, 'model_used', None),
                "metadata": getattr(message, 'metadata', {})
            }
            export_data["messages"].append(msg_data)
        
        return json.dumps(export_data, indent=2).encode('utf-8')
    
    def _export_as_csv(self, messages: List[Message]) -> bytes:
        """Export messages as CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Timestamp', 'Role', 'Content', 'Model Used'])
        
        # Write messages
        for message in messages:
            timestamp = message.created_at.isoformat() if hasattr(message, 'created_at') else ''
            writer.writerow([
                timestamp,
                message.role,
                message.content,
                getattr(message, 'model_used', '')
            ])
        
        return output.getvalue().encode('utf-8')


def inject_chat_css() -> None:
    """Inject additional CSS for enhanced chat interface"""
    css = """
    <style>
    /* Enhanced chat interface styles */
    .chat-container {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid var(--border-color, #e0e0e0);
        border-radius: 0.5rem;
        background-color: var(--background-color, #ffffff);
    }
    
    /* Streaming message animation */
    .message-bubble.streaming {
        animation: pulse 1.5s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    /* Typing indicator */
    .typing-indicator {
        display: inline-flex;
        align-items: center;
    }
    
    .typing-indicator span {
        height: 8px;
        width: 8px;
        border-radius: 50%;
        background-color: var(--text-color, #333);
        display: inline-block;
        margin: 0 2px;
        opacity: 0.4;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-indicator span:nth-child(1) { animation-delay: 0s; }
    .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
    .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
    
    @keyframes typing {
        0%, 60%, 100% {
            transform: translateY(0);
            opacity: 0.4;
        }
        30% {
            transform: translateY(-10px);
            opacity: 1;
        }
    }
    
    /* File attachment styling */
    .stFileUploader > div {
        border: 2px dashed var(--border-color, #e0e0e0);
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
        transition: border-color 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        border-color: var(--primary-color, #1f77b4);
    }
    
    /* Enhanced message bubbles */
    .message-bubble {
        position: relative;
        margin: 1rem 0;
        padding: 1rem;
        border-radius: 1rem;
        box-shadow: 0 2px 8px var(--shadow-color, rgba(0,0,0,0.1));
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Welcome message special styling */
    .message-bubble.welcome {
        background: linear-gradient(135deg, var(--ai-msg-bg, #f5f5f5) 0%, var(--secondary-bg, #f8f9fa) 100%);
        border: 1px solid var(--primary-color, #1f77b4);
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .chat-container {
            max-height: 400px;
            padding: 0.5rem;
        }
        
        .message-bubble {
            padding: 0.75rem;
            margin: 0.5rem 0;
        }
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)