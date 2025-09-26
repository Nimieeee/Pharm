"""
UI Components for the pharmacology chat application.
Provides responsive, themed components for chat interface.
"""
import streamlit as st
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re


@dataclass
class Message:
    """Message data structure for chat interface."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    model_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatInterface:
    """Main chat interface components with responsive design."""
    
    def __init__(self, theme_manager):
        self.theme_manager = theme_manager
    
    def render_chat_container(self) -> None:
        """Render the main chat container with proper styling."""
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    def render_message_bubble(self, message: Message) -> None:
        """Render a single message bubble with appropriate styling."""
        bubble_class = "user-message" if message.role == "user" else "ai-message"
        role_display = "You" if message.role == "user" else "AI Assistant"
        
        # Format timestamp
        time_str = message.timestamp.strftime("%H:%M")
        
        # Add model info for AI messages
        model_info = ""
        if message.role == "assistant" and message.model_used:
            model_info = f" • {message.model_used}"
        
        message_html = f"""
        <div class="message-bubble {bubble_class}">
            <div class="message-role">{role_display}{model_info} • {time_str}</div>
            <div class="message-content">{self._format_message_content(message.content)}</div>
        </div>
        """
        
        st.markdown(message_html, unsafe_allow_html=True)
    
    def render_chat_history(self, messages: List[Message]) -> None:
        """Render the complete chat history."""
        if not messages:
            self._render_welcome_message()
            return
        
        for message in messages:
            self.render_message_bubble(message)
    
    def render_message_input(self, placeholder: str = "Ask about pharmacology...") -> Optional[str]:
        """Render message input with send button."""
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_input = st.text_input(
                    "Message",
                    placeholder=placeholder,
                    key="message_input",
                    label_visibility="collapsed"
                )
            
            with col2:
                send_button = st.button("Send", key="send_button", use_container_width=True)
            
            if send_button and user_input.strip():
                return user_input.strip()
            
            return None
    
    def render_typing_indicator(self) -> None:
        """Render typing indicator for AI responses."""
        typing_html = """
        <div class="message-bubble ai-message">
            <div class="message-role">AI Assistant</div>
            <div class="message-content">
                <span class="loading-dots">Thinking</span>
            </div>
        </div>
        """
        st.markdown(typing_html, unsafe_allow_html=True)
    
    def render_model_selector(self, current_model: str, available_models: List[Dict[str, str]]) -> str:
        """Render model toggle switch interface."""
        st.markdown('<div class="model-selector">', unsafe_allow_html=True)
        
        # Determine current state based on model
        is_premium = current_model in ["qwen/qwen3-32b", "qwen3-32b", "premium"]
        
        # Create toggle switch HTML
        toggle_html = self._create_toggle_switch_html(is_premium)
        st.markdown(toggle_html, unsafe_allow_html=True)
        
        # Handle toggle state change
        toggle_key = "model_toggle_switch"
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
            if new_state:
                st.success("✅ Switched to Premium Mode")
            else:
                st.success("✅ Switched to Fast Mode")
            # Store the preference for session persistence
            st.session_state["selected_model"] = "qwen/qwen3-32b" if new_state else "gemma2-9b-it"
            st.rerun()
        
        # Return appropriate model ID based on current state
        selected_model = "qwen/qwen3-32b" if st.session_state[toggle_key] else "gemma2-9b-it"
        
        # Update session state for persistence
        st.session_state["selected_model"] = selected_model
        
        st.markdown('</div>', unsafe_allow_html=True)
        return selected_model
    
    def _create_toggle_switch_html(self, is_premium: bool) -> str:
        """Create HTML for the toggle switch with labels."""
        checked = "checked" if is_premium else ""
        
        return f"""
        <div class="model-toggle-container">
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
                {'High-quality responses for complex topics' if is_premium else 'Quick responses for general questions'}
            </div>
        </div>
        """
    
    def render_status_indicator(self, status: str, message: str = "") -> None:
        """Render connection/status indicator."""
        status_class = f"status-{status}"
        status_text = {
            "online": "Connected",
            "offline": "Disconnected", 
            "loading": "Connecting..."
        }.get(status, status)
        
        status_html = f"""
        <div style="display: flex; align-items: center; margin: 0.5rem 0;">
            <span class="status-indicator {status_class}"></span>
            <span style="font-size: 0.8rem; opacity: 0.8;">{status_text}</span>
            {f"<span style='margin-left: 0.5rem; font-size: 0.8rem;'>{message}</span>" if message else ""}
        </div>
        """
        st.markdown(status_html, unsafe_allow_html=True)
    
    def render_conversation_controls(self) -> Dict[str, bool]:
        """Render conversation control buttons."""
        col1, col2, col3 = st.columns([1, 1, 1])
        
        controls = {}
        
        with col1:
            controls["clear"] = st.button("Clear Chat", key="clear_chat")
        
        with col2:
            controls["export"] = st.button("Export", key="export_chat")
        
        with col3:
            controls["settings"] = st.button("Settings", key="chat_settings")
        
        return controls
    
    def _format_message_content(self, content: str) -> str:
        """Format message content with proper HTML escaping and markdown-like formatting."""
        # Escape HTML
        content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # Convert markdown-like formatting
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', content)
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)
        
        # Convert line breaks
        content = content.replace('\n', '<br>')
        
        return content
    
    def _render_welcome_message(self) -> None:
        """Render welcome message when no chat history exists."""
        welcome_html = """
        <div class="message-bubble ai-message">
            <div class="message-role">AI Assistant</div>
            <div class="message-content">
                <strong>Welcome to Pharmacology Chat!</strong><br><br>
                I'm here to help you with pharmacology questions. You can ask me about:
                <ul>
                    <li>Drug mechanisms and interactions</li>
                    <li>Pharmacokinetics and pharmacodynamics</li>
                    <li>Clinical applications and dosing</li>
                    <li>Side effects and contraindications</li>
                </ul>
                What would you like to know?
            </div>
        </div>
        """
        st.markdown(welcome_html, unsafe_allow_html=True)


class AuthInterface:
    """Authentication interface components."""
    
    def __init__(self, theme_manager):
        self.theme_manager = theme_manager
    
    def render_login_form(self) -> Dict[str, str]:
        """Render login form and return credentials if submitted."""
        st.markdown("### Sign In")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your.email@example.com")
            password = st.text_input("Password", type="password")
            
            col1, col2 = st.columns(2)
            with col1:
                login_button = st.form_submit_button("Sign In", use_container_width=True)
            with col2:
                signup_button = st.form_submit_button("Sign Up", use_container_width=True)
            
            if login_button and email and password:
                return {"action": "login", "email": email, "password": password}
            elif signup_button and email and password:
                return {"action": "signup", "email": email, "password": password}
        
        return {}
    
    def render_user_profile(self, user_email: str) -> bool:
        """Render user profile section with logout option."""
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**Signed in as:**")
            st.markdown(f"`{user_email}`")
            
            logout_button = st.button("Sign Out", key="logout_button", use_container_width=True)
            
            return logout_button


class SettingsInterface:
    """Settings and preferences interface."""
    
    def __init__(self, theme_manager):
        self.theme_manager = theme_manager
    
    def render_settings_panel(self) -> Dict[str, Any]:
        """Render settings panel in sidebar."""
        settings = {}
        
        with st.sidebar:
            st.markdown("### Settings")
            
            # Theme selection removed - permanent dark theme
            st.markdown("**Theme:** Dark Mode (Permanent)")
            
            # Chat preferences
            st.markdown("#### Chat Preferences")
            settings["show_timestamps"] = st.checkbox("Show timestamps", value=True)
            settings["show_model_info"] = st.checkbox("Show model information", value=True)
            settings["auto_scroll"] = st.checkbox("Auto-scroll to new messages", value=True)
            
            # Advanced settings
            with st.expander("Advanced"):
                settings["max_history"] = st.slider("Max conversation history", 10, 100, 50)
                settings["response_timeout"] = st.slider("Response timeout (seconds)", 10, 60, 30)
        
        return settings


class ResponsiveLayout:
    """Responsive layout utilities for different screen sizes."""
    
    @staticmethod
    def get_layout_config() -> Dict[str, Any]:
        """Get layout configuration based on screen size."""
        # This would ideally use JavaScript to detect screen size
        # For now, we'll use Streamlit's responsive behavior
        return {
            "sidebar_width": 300,
            "main_width": 800,
            "mobile_breakpoint": 768,
            "tablet_breakpoint": 1024
        }
    
    @staticmethod
    def render_mobile_header() -> None:
        """Render mobile-optimized header."""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("☰", key="mobile_menu"):
                st.session_state.show_sidebar = not st.session_state.get("show_sidebar", False)
        
        with col2:
            st.markdown("**Pharmacology Chat**")
        
        with col3:
            # Theme toggle removed - permanent dark theme
            st.markdown("🌙")  # Dark mode indicator
    
    @staticmethod
    def apply_responsive_css() -> str:
        """Generate responsive CSS for mobile and tablet layouts."""
        return """
        <style>
        /* Mobile-first responsive design */
        @media (max-width: 480px) {
            .stApp > header {
                display: none;
            }
            
            .main .block-container {
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }
            
            .stTextInput > div > div > input {
                font-size: 16px; /* Prevent zoom on iOS */
            }
        }
        
        @media (max-width: 768px) {
            .chat-container {
                max-width: 100%;
                padding: 0.5rem;
            }
            
            .message-bubble {
                margin: 0.5rem 0;
                padding: 0.75rem;
            }
        }
        
        @media (min-width: 1024px) {
            .chat-container {
                max-width: 900px;
            }
        }
        </style>
        """