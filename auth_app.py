"""
Main Authentication App Integration
Demonstrates the complete authentication system integration
"""

import streamlit as st

# Import authentication components
from auth_manager import AuthenticationManager
from session_manager import SessionManager
from auth_ui import AuthInterface, require_authentication
from auth_guard import AuthGuard, RouteProtection

def initialize_auth_system():
    """Initialize the authentication system components"""
    # Initialize managers
    auth_manager = AuthenticationManager()
    session_manager = SessionManager(auth_manager)
    auth_guard = AuthGuard(auth_manager, session_manager)
    auth_ui = AuthInterface(auth_manager, session_manager)
    
    return auth_manager, session_manager, auth_guard, auth_ui

def render_chat_placeholder():
    """Placeholder for chat interface (to be implemented in later tasks)"""
    st.title("💬 Pharmacology Chat")
    st.success("🎉 Authentication successful! Chat interface will be implemented in the next tasks.")
    
    # Show current user info
    st.info("You are now authenticated and can access the chat interface.")
    
    # Placeholder chat interface
    st.markdown("---")
    st.subheader("Chat Interface (Coming Soon)")
    
    # Mock conversation
    with st.container():
        st.markdown("**You:** What is the mechanism of action of aspirin?")
        st.markdown("**AI:** *Chat functionality will be available after implementing the RAG pipeline and model management...*")
    
    # Message input placeholder
    st.text_input("Type your pharmacology question here...", disabled=True, 
                 help="Chat functionality will be enabled in upcoming tasks")

def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Pharmacology Chat Assistant",
        page_icon="🧬",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize authentication system
    auth_manager, session_manager, auth_guard, auth_ui = initialize_auth_system()
    
    # Check authentication state
    auth_state = auth_guard.check_auth_state()
    
    if auth_state == "authenticated":
        # User is authenticated - show main app
        
        # Render user profile in sidebar
        auth_ui.render_user_profile()
        
        # Main content area
        if RouteProtection.protect_chat_interface(auth_guard):
            render_chat_placeholder()
    
    else:
        # User is not authenticated - show auth page
        auth_ui.render_auth_page()
    
    # Add some styling
    st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()