"""
Demo application showcasing the responsive UI with theme support.
This demonstrates all the UI components and styling features.
"""
import streamlit as st
from datetime import datetime
from theme_manager import ThemeManager
from ui_components import ChatInterface, AuthInterface, SettingsInterface, ResponsiveLayout, Message
from styles import StyleGenerator


def main():
    """Main demo application."""
    st.set_page_config(
        page_title="Pharmacology Chat - UI Demo",
        page_icon="💊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize theme manager
    theme_manager = ThemeManager()
    
    # Apply theme and styles
    theme_config = theme_manager.get_theme_config()
    
    # Apply all styles
    st.markdown(StyleGenerator.generate_base_styles(theme_config), unsafe_allow_html=True)
    st.markdown(StyleGenerator.generate_chat_styles(), unsafe_allow_html=True)
    st.markdown(StyleGenerator.generate_form_styles(), unsafe_allow_html=True)
    st.markdown(StyleGenerator.generate_layout_styles(), unsafe_allow_html=True)
    st.markdown(StyleGenerator.generate_responsive_styles(), unsafe_allow_html=True)
    st.markdown(StyleGenerator.generate_accessibility_styles(), unsafe_allow_html=True)
    
    # Initialize UI components
    chat_interface = ChatInterface(theme_manager)
    auth_interface = AuthInterface(theme_manager)
    settings_interface = SettingsInterface(theme_manager)
    
    # Theme toggle in header
    theme_manager.render_theme_toggle()
    
    # Demo mode selector
    demo_mode = st.sidebar.selectbox(
        "Demo Mode",
        ["Chat Interface", "Authentication", "Settings", "All Components"]
    )
    
    if demo_mode == "Chat Interface":
        demo_chat_interface(chat_interface)
    elif demo_mode == "Authentication":
        demo_auth_interface(auth_interface)
    elif demo_mode == "Settings":
        demo_settings_interface(settings_interface)
    else:
        demo_all_components(chat_interface, auth_interface, settings_interface)


def demo_chat_interface(chat_interface: ChatInterface):
    """Demo the chat interface components."""
    st.title("💊 Pharmacology Chat Interface Demo")
    
    # Model selector demo
    available_models = [
        {"id": "gemma2-9b-it", "name": "Fast Mode (Gemma2-9B)", "description": "Quick responses for general questions"},
        {"id": "qwen3-32b", "name": "Premium Mode (Qwen3-32B)", "description": "Detailed responses for complex topics"}
    ]
    
    selected_model = chat_interface.render_model_selector("gemma2-9b-it", available_models)
    
    # Status indicator demo
    status_options = ["online", "offline", "loading"]
    status = st.sidebar.selectbox("Connection Status", status_options)
    chat_interface.render_status_indicator(status, "Demo mode active")
    
    # Sample messages for demo
    sample_messages = [
        Message(
            role="assistant",
            content="Welcome to Pharmacology Chat! I'm here to help you with pharmacology questions. You can ask me about:\n\n• Drug mechanisms and interactions\n• Pharmacokinetics and pharmacodynamics\n• Clinical applications and dosing\n• Side effects and contraindications\n\nWhat would you like to know?",
            timestamp=datetime.now(),
            model_used="AI Assistant"
        ),
        Message(
            role="user",
            content="Can you explain how ACE inhibitors work and their common side effects?",
            timestamp=datetime.now()
        ),
        Message(
            role="assistant",
            content="**ACE Inhibitors (Angiotensin-Converting Enzyme Inhibitors)**\n\n**Mechanism of Action:**\nACE inhibitors work by blocking the angiotensin-converting enzyme, which prevents the conversion of angiotensin I to angiotensin II. This results in:\n\n• Vasodilation (reduced peripheral resistance)\n• Decreased aldosterone secretion\n• Reduced sodium and water retention\n• Lower blood pressure\n\n**Common Side Effects:**\n• **Dry cough** (10-15% of patients) - due to increased bradykinin\n• Hyperkalemia (elevated potassium)\n• Hypotension, especially first-dose\n• Angioedema (rare but serious)\n• Renal impairment in susceptible patients\n\n**Examples:** Lisinopril, Enalapril, Captopril\n\nWould you like me to explain more about any specific aspect?",
            timestamp=datetime.now(),
            model_used="Qwen3-32B"
        )
    ]
    
    # Chat container
    chat_interface.render_chat_container()
    
    # Display sample messages
    for message in sample_messages:
        chat_interface.render_message_bubble(message)
    
    # Show typing indicator if loading
    if status == "loading":
        chat_interface.render_typing_indicator()
    
    # Message input
    user_message = chat_interface.render_message_input("Ask about pharmacology...")
    if user_message:
        st.success(f"You would send: {user_message}")
    
    # Conversation controls
    controls = chat_interface.render_conversation_controls()
    if any(controls.values()):
        st.info(f"Controls clicked: {[k for k, v in controls.items() if v]}")


def demo_auth_interface(auth_interface: AuthInterface):
    """Demo the authentication interface."""
    st.title("🔐 Authentication Interface Demo")
    
    # Simulate authentication state
    if "demo_authenticated" not in st.session_state:
        st.session_state.demo_authenticated = False
    
    if not st.session_state.demo_authenticated:
        st.markdown("### Please sign in to continue")
        
        credentials = auth_interface.render_login_form()
        
        if credentials:
            if credentials["action"] == "login":
                st.session_state.demo_authenticated = True
                st.session_state.demo_user_email = credentials["email"]
                st.success("Successfully signed in!")
                st.rerun()
            elif credentials["action"] == "signup":
                st.session_state.demo_authenticated = True
                st.session_state.demo_user_email = credentials["email"]
                st.success("Account created and signed in!")
                st.rerun()
    else:
        st.success("You are signed in!")
        
        # Show user profile
        logout = auth_interface.render_user_profile(st.session_state.demo_user_email)
        
        if logout:
            st.session_state.demo_authenticated = False
            if "demo_user_email" in st.session_state:
                del st.session_state.demo_user_email
            st.info("Signed out successfully!")
            st.rerun()
        
        # Show what authenticated users would see
        st.markdown("---")
        st.markdown("### Authenticated User Content")
        st.markdown("This is where the chat interface would appear for authenticated users.")


def demo_settings_interface(settings_interface: SettingsInterface):
    """Demo the settings interface."""
    st.title("⚙️ Settings Interface Demo")
    
    settings = settings_interface.render_settings_panel()
    
    # Display current settings
    st.markdown("### Current Settings")
    for key, value in settings.items():
        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    
    # Theme demonstration
    st.markdown("---")
    st.markdown("### Theme Demonstration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Sample Content")
        st.info("This is an info message")
        st.success("This is a success message")
        st.warning("This is a warning message")
        st.error("This is an error message")
    
    with col2:
        st.markdown("#### Interactive Elements")
        st.button("Sample Button")
        st.text_input("Sample Input", placeholder="Type here...")
        st.selectbox("Sample Select", ["Option 1", "Option 2", "Option 3"])


def demo_all_components(chat_interface: ChatInterface, auth_interface: AuthInterface, settings_interface: SettingsInterface):
    """Demo all components together."""
    st.title("🎨 Complete UI Component Demo")
    
    # Create tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Chat", "Authentication", "Settings", "Responsive"])
    
    with tab1:
        st.markdown("### Chat Interface Components")
        demo_chat_interface(chat_interface)
    
    with tab2:
        st.markdown("### Authentication Components")
        demo_auth_interface(auth_interface)
    
    with tab3:
        st.markdown("### Settings Components")
        demo_settings_interface(settings_interface)
    
    with tab4:
        st.markdown("### Responsive Design Demo")
        st.markdown("Resize your browser window to see responsive behavior:")
        
        # Show different layouts
        st.markdown("#### Desktop Layout (>1024px)")
        st.info("Full sidebar, wide chat container, large message bubbles")
        
        st.markdown("#### Tablet Layout (768px - 1024px)")
        st.info("Collapsible sidebar, medium chat container, adjusted message bubbles")
        
        st.markdown("#### Mobile Layout (<768px)")
        st.info("Hidden sidebar, full-width container, stacked elements")
        
        # Responsive grid demo
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.markdown("**Sidebar**")
            st.markdown("Settings and controls")
        
        with col2:
            st.markdown("**Main Content**")
            st.markdown("Chat interface and messages")
        
        with col3:
            st.markdown("**Actions**")
            st.markdown("Quick actions and status")


if __name__ == "__main__":
    main()