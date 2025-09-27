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
        Render the complete chat history with unlimited message display
        
        Args:
            messages: List of Message objects to display
        """
        if not messages and not st.session_state.show_typing_indicator:
            self._render_welcome_message()
            return
        
        # Show unlimited history header
        self._render_unlimited_history_header(len(messages))
        
        # Create unlimited scrolling container for chat messages
        st.markdown(
            '<div class="unlimited-chat-container" id="unlimited-chat-container">',
            unsafe_allow_html=True
        )
        
        # Create a container for chat messages
        chat_container = st.container()
        
        with chat_container:
            # Render all historical messages without pagination
            for message in messages:
                self._render_message_bubble(message)
            
            # Render streaming message if active
            if st.session_state.streaming_message:
                self._render_streaming_message(st.session_state.streaming_message)
            
            # Render typing indicator if active
            elif st.session_state.show_typing_indicator:
                self._render_typing_indicator()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
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
        Render conversation management controls with unlimited history support
        
        Args:
            user_id: Current user ID
            chat_manager: ChatManager instance
            
        Returns:
            Dictionary of control actions triggered
        """
        st.markdown("### 💬 Conversation Controls")
        
        # Show unlimited history status
        st.info("📜 **Unlimited History Mode** - Showing complete conversation without pagination")
        
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
    
    def render_model_toggle_switch(self, current_model: str, on_change_callback=None) -> str:
        """
        Render model toggle switch interface (replaces dropdown)
        
        Args:
            current_model: Currently selected model
            on_change_callback: Callback function when model changes
            
        Returns:
            Selected model identifier
        """
        # Determine current state based on model
        is_premium = current_model in ["qwen/qwen3-32b", "qwen3-32b", "premium"]
        
        # Create toggle switch HTML
        toggle_html = self._create_model_toggle_switch_html(is_premium)
        st.markdown(toggle_html, unsafe_allow_html=True)
        
        # Handle toggle state change
        toggle_key = "chat_model_toggle_switch"
        if toggle_key not in st.session_state:
            st.session_state[toggle_key] = is_premium
        
        # Create invisible checkbox to capture state changes
        new_state = st.checkbox(
            "Toggle Model",
            value=st.session_state[toggle_key],
            key=f"{toggle_key}_checkbox",
            label_visibility="collapsed"
        )
        
        # Update session state and provide visual feedback
        if new_state != st.session_state[toggle_key]:
            st.session_state[toggle_key] = new_state
            selected_model = "premium" if new_state else "fast"
            
            # Call callback if provided
            if on_change_callback:
                on_change_callback(selected_model)
            
            # Store the preference for session persistence
            st.session_state["selected_model"] = selected_model
            st.rerun()
        
        # Return appropriate model ID based on current state
        selected_model = "premium" if st.session_state[toggle_key] else "fast"
        
        # Update session state for persistence
        st.session_state["selected_model"] = selected_model
        
        return selected_model
    
    def render_header_model_toggle(self, current_model: str, on_change_callback=None) -> str:
        """
        Render compact model toggle switch for chat header
        
        Args:
            current_model: Currently selected model
            on_change_callback: Callback function when model changes
            
        Returns:
            Selected model identifier
        """
        # Determine current state based on model
        is_premium = current_model in ["qwen/qwen3-32b", "qwen3-32b", "premium"]
        
        # Create compact toggle switch HTML for header
        toggle_html = self._create_header_model_toggle_html(is_premium)
        st.markdown(toggle_html, unsafe_allow_html=True)
        
        # Handle toggle state change
        toggle_key = "header_model_toggle_switch"
        if toggle_key not in st.session_state:
            st.session_state[toggle_key] = is_premium
        
        # Create invisible checkbox to capture state changes
        new_state = st.checkbox(
            "Header Toggle Model",
            value=st.session_state[toggle_key],
            key=f"{toggle_key}_checkbox",
            label_visibility="collapsed"
        )
        
        # Update session state and provide visual feedback
        if new_state != st.session_state[toggle_key]:
            st.session_state[toggle_key] = new_state
            selected_model = "premium" if new_state else "fast"
            
            # Call callback if provided
            if on_change_callback:
                on_change_callback(selected_model)
            
            # Store the preference for session persistence
            st.session_state["selected_model"] = selected_model
            st.rerun()
        
        # Return appropriate model ID based on current state
        selected_model = "premium" if st.session_state[toggle_key] else "fast"
        
        return selected_model
    

    
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
            const chatContainer = document.getElementById('chat-container') || document.getElementById('unlimited-chat-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
        
        // Scroll after a short delay to ensure content is rendered
        setTimeout(scrollToBottom, 100);
        </script>
        """
        st.markdown(scroll_script, unsafe_allow_html=True)
    
    def _create_model_toggle_switch_html(self, is_premium: bool) -> str:
        """Create HTML for the model toggle switch with labels."""
        checked = "checked" if is_premium else ""
        
        return f"""
        <div class="model-toggle-container">
            <div class="model-toggle-header">
                <h4>🤖 AI Model Selection</h4>
            </div>
            <div class="model-toggle-labels">
                <span class="toggle-label {'active' if not is_premium else ''}">⚡ Fast</span>
                <div class="toggle-switch-wrapper">
                    <label class="toggle-switch">
                        <input type="checkbox" {checked} onchange="
                            const checkbox = document.querySelector('[data-testid=\\'stCheckbox\\'] input');
                            if (checkbox) checkbox.click();
                        ">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <span class="toggle-label {'active' if is_premium else ''}">🎯 Premium</span>
            </div>
            <div class="model-description">
                {'High-quality responses with 8,000 token limit for complex topics' if is_premium else 'Quick responses for general questions'}
            </div>
        </div>
        """
    
    def _create_header_model_toggle_html(self, is_premium: bool) -> str:
        """Create compact HTML for the header model toggle switch."""
        checked = "checked" if is_premium else ""
        
        return f"""
        <div class="header-model-toggle">
            <div class="model-toggle-labels compact">
                <span class="toggle-label {'active' if not is_premium else ''}">⚡</span>
                <div class="toggle-switch-wrapper">
                    <label class="toggle-switch compact">
                        <input type="checkbox" {checked} onchange="
                            const checkbox = document.querySelector('[data-testid=\\'stCheckbox\\']:last-of-type input');
                            if (checkbox) checkbox.click();
                        ">
                        <span class="toggle-slider"></span>
                    </label>
                </div>
                <span class="toggle-label {'active' if is_premium else ''}">🎯</span>
            </div>
            <div class="model-status-text">
                {'Premium Mode' if is_premium else 'Fast Mode'}
            </div>
        </div>
        """
    
    def _render_unlimited_history_header(self, message_count: int) -> None:
        """Render header for unlimited conversation history"""
        st.markdown("#### 📜 Complete Conversation History")
        if message_count > 0:
            st.caption(f"Displaying all {message_count} messages without pagination")
        else:
            st.caption("No messages yet - start a conversation!")
    
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
    """Inject additional CSS for enhanced chat interface with dark theme and unlimited history"""
    css = """
    <style>
    /* Enhanced chat interface styles with permanent dark theme */
    .chat-container, .unlimited-chat-container {
        max-height: 70vh;
        overflow-y: auto;
        overflow-x: hidden;
        padding: 1rem;
        border: 1px solid var(--border-color, #4b5563);
        border-radius: 0.5rem;
        background-color: var(--background-color, #0e1117);
        scroll-behavior: smooth;
        /* Performance optimizations for unlimited scrolling */
        contain: layout style paint;
        will-change: scroll-position;
        transform: translateZ(0);
    }
    
    /* Custom scrollbar for dark theme */
    .chat-container::-webkit-scrollbar,
    .unlimited-chat-container::-webkit-scrollbar {
        width: 8px;
    }
    
    .chat-container::-webkit-scrollbar-track,
    .unlimited-chat-container::-webkit-scrollbar-track {
        background: var(--secondary-bg, #262730);
        border-radius: 4px;
    }
    
    .chat-container::-webkit-scrollbar-thumb,
    .unlimited-chat-container::-webkit-scrollbar-thumb {
        background: var(--border-color, #4b5563);
        border-radius: 4px;
    }
    
    .chat-container::-webkit-scrollbar-thumb:hover,
    .unlimited-chat-container::-webkit-scrollbar-thumb:hover {
        background: var(--primary-color, #4fc3f7);
    }
    
    /* Model Toggle Switch Styles */
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
        background-color: var(--primary-color, #4fc3f7);
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
    
    /* File attachment styling with dark theme */
    .stFileUploader > div {
        border: 2px dashed var(--border-color, #4b5563);
        border-radius: 0.5rem;
        padding: 1rem;
        text-align: center;
        transition: border-color 0.3s ease;
        background-color: var(--secondary-bg, #262730);
    }
    
    .stFileUploader > div:hover {
        border-color: var(--primary-color, #4fc3f7);
    }
    
    /* Enhanced message bubbles with dark theme */
    .message-bubble {
        position: relative;
        margin: 1rem 0;
        padding: 1rem;
        border-radius: 1rem;
        box-shadow: 0 2px 8px var(--shadow-color, rgba(0,0,0,0.4));
        animation: slideIn 0.3s ease-out;
        /* Performance optimization for unlimited scrolling */
        contain: layout style paint;
        transform: translateZ(0);
        backface-visibility: hidden;
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
    
    /* Welcome message special styling with dark theme */
    .message-bubble.welcome {
        background: linear-gradient(135deg, var(--ai-msg-bg, #374151) 0%, var(--secondary-bg, #262730) 100%);
        border: 1px solid var(--primary-color, #4fc3f7);
    }
    
    /* Conversation tabs integration */
    .conversation-tab-content {
        background-color: var(--background-color, #0e1117);
        border-radius: 0.5rem;
        padding: 1rem;
        margin-top: 1rem;
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
    
    /* Responsive adjustments for dark theme */
    @media (max-width: 768px) {
        .chat-container, .unlimited-chat-container {
            max-height: 60vh;
            padding: 0.5rem;
        }
        
        .message-bubble {
            padding: 0.75rem;
            margin: 0.5rem 0;
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
        .chat-container, .unlimited-chat-container {
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