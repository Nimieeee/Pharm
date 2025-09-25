"""
UI Integration module that combines all theme and component systems.
This is the main entry point for using the responsive UI with theme support.
"""
import streamlit as st
from datetime import datetime
from typing import List, Dict, Any, Optional
from theme_manager import ThemeManager
from ui_components import ChatInterface, AuthInterface, SettingsInterface, ResponsiveLayout, Message
from styles import StyleGenerator


class PharmacologyUI:
    """Main UI class that integrates all components with theme support."""
    
    def __init__(self):
        """Initialize the UI system."""
        self.theme_manager = ThemeManager()
        self.chat_interface = ChatInterface(self.theme_manager)
        self.auth_interface = AuthInterface(self.theme_manager)
        self.settings_interface = SettingsInterface(self.theme_manager)
        
        # Apply all styles
        self._apply_styles()
    
    def _apply_styles(self):
        """Apply all CSS styles based on current theme."""
        theme_config = self.theme_manager.get_theme_config()
        
        # Apply all style components
        st.markdown(StyleGenerator.generate_base_styles(theme_config), unsafe_allow_html=True)
        st.markdown(StyleGenerator.generate_chat_styles(), unsafe_allow_html=True)
        st.markdown(StyleGenerator.generate_form_styles(), unsafe_allow_html=True)
        st.markdown(StyleGenerator.generate_layout_styles(), unsafe_allow_html=True)
        st.markdown(StyleGenerator.generate_responsive_styles(), unsafe_allow_html=True)
        st.markdown(StyleGenerator.generate_accessibility_styles(), unsafe_allow_html=True)
    
    def render_header(self):
        """Render the application header with theme toggle."""
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.title("💊 Pharmacology Chat")
        
        with col3:
            self.theme_manager.render_theme_toggle()
    
    def render_chat_page(self, messages: List[Message], available_models: List[Dict[str, str]], 
                        current_model: str, connection_status: str = "online"):
        """Render the main chat interface."""
        # Model selector
        selected_model = self.chat_interface.render_model_selector(current_model, available_models)
        
        # Connection status
        self.chat_interface.render_status_indicator(connection_status)
        
        # Chat container
        self.chat_interface.render_chat_container()
        
        # Chat history
        self.chat_interface.render_chat_history(messages)
        
        # Message input
        user_input = self.chat_interface.render_message_input()
        
        # Conversation controls
        controls = self.chat_interface.render_conversation_controls()
        
        return {
            "selected_model": selected_model,
            "user_input": user_input,
            "controls": controls
        }
    
    def render_auth_page(self):
        """Render authentication interface."""
        if not st.session_state.get("authenticated", False):
            credentials = self.auth_interface.render_login_form()
            return {"action": "login", "credentials": credentials}
        else:
            logout = self.auth_interface.render_user_profile(
                st.session_state.get("user_email", "")
            )
            if logout:
                return {"action": "logout"}
        return {"action": "none"}
    
    def render_settings_sidebar(self):
        """Render settings in sidebar."""
        settings = self.settings_interface.render_settings_panel()
        
        # Handle theme changes
        if settings.get("theme_changed"):
            self._apply_styles()
            st.rerun()
        
        return settings
    
    def create_message(self, role: str, content: str, model_used: str = None) -> Message:
        """Create a new message object."""
        return Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            model_used=model_used
        )
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self.theme_manager.get_current_theme()
    
    def apply_responsive_layout(self):
        """Apply responsive layout adjustments."""
        # Add responsive CSS
        st.markdown(ResponsiveLayout.apply_responsive_css(), unsafe_allow_html=True)
        
        # Mobile header if needed
        if st.session_state.get("mobile_view", False):
            ResponsiveLayout.render_mobile_header()


def initialize_ui() -> PharmacologyUI:
    """Initialize and return the UI system."""
    # Configure Streamlit page
    st.set_page_config(
        page_title="Pharmacology Chat",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Create and return UI instance
    return PharmacologyUI()


# Example usage function
def example_chat_app():
    """Example implementation of a complete chat app using the UI system."""
    # Initialize UI
    ui = initialize_ui()
    
    # Render header
    ui.render_header()
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # Handle authentication
    if not st.session_state.authenticated:
        auth_result = ui.render_auth_page()
        if auth_result["action"] == "login" and auth_result["credentials"]:
            # Simulate authentication
            st.session_state.authenticated = True
            st.session_state.user_email = auth_result["credentials"]["email"]
            st.rerun()
        return
    
    # Render settings sidebar
    settings = ui.render_settings_sidebar()
    
    # Sample models
    available_models = [
        {"id": "gemma2-9b-it", "name": "Fast Mode", "description": "Quick responses"},
        {"id": "qwen3-32b", "name": "Premium Mode", "description": "Detailed responses"}
    ]
    
    # Render main chat interface
    chat_result = ui.render_chat_page(
        messages=st.session_state.messages,
        available_models=available_models,
        current_model=st.session_state.get("selected_model", "gemma2-9b-it"),
        connection_status="online"
    )
    
    # Handle user input
    if chat_result["user_input"]:
        # Add user message
        user_msg = ui.create_message("user", chat_result["user_input"])
        st.session_state.messages.append(user_msg)
        
        # Simulate AI response
        ai_response = f"This is a simulated response to: {chat_result['user_input']}"
        ai_msg = ui.create_message("assistant", ai_response, chat_result["selected_model"])
        st.session_state.messages.append(ai_msg)
        
        st.rerun()
    
    # Handle controls
    if chat_result["controls"]["clear"]:
        st.session_state.messages = []
        st.rerun()
    
    # Handle logout
    auth_result = ui.render_auth_page()
    if auth_result["action"] == "logout":
        st.session_state.authenticated = False
        st.session_state.messages = []
        if "user_email" in st.session_state:
            del st.session_state.user_email
        st.rerun()


if __name__ == "__main__":
    example_chat_app()