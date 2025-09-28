"""
Simple Chatbot Application
A clean Streamlit chatbot with dark mode, model switching, and RAG functionality
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import time

# Import our core modules with error handling
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# System info (hidden in production)

try:
    import models
    from models import ModelManager
except ImportError as e:
    st.error(f"Cannot import ModelManager: {e}")
    st.error(f"Current working directory: {os.getcwd()}")
    st.error(f"Python path: {sys.path}")
    st.error(f"Files in current directory: {os.listdir('.')}")
    st.stop()

try:
    import rag
    from rag import RAGManager
except ImportError as e:
    st.error(f"Cannot import RAGManager: {e}")
    st.stop()

try:
    from conversation_manager import ConversationManager
except ImportError as e:
    st.error(f"Cannot import ConversationManager: {e}")
    st.stop()

try:
    from database import SimpleChatbotDB
except ImportError as e:
    st.error(f"Cannot import SimpleChatbotDB: {e}")
    st.stop()

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(
    page_title="PharmGPT",
    page_icon="PharmGPT.png",
    layout="wide",
    initial_sidebar_state=st.session_state.get("sidebar_state", "expanded")
)

# Initialize theme state - respects system settings by default
if "theme_override" not in st.session_state:
    st.session_state.theme_override = "system"  # "system", "light", or "dark"

# ----------------------------
# Theme System with Light/Dark Support
# ----------------------------

def render_theme_toggle():
    """Render animated theme toggle button in sidebar"""
    st.sidebar.markdown("### 🎨 Theme")
    
    # Get current theme for button state
    current_theme = st.session_state.theme_override
    
    # Determine button state and next theme
    if current_theme == "system":
        button_state = "auto"
        next_theme = "light"
        tooltip = "System (Auto)"
    elif current_theme == "light":
        button_state = "light"
        next_theme = "dark"
        tooltip = "Light Mode"
    else:  # dark
        button_state = "dark"
        next_theme = "system"
        tooltip = "Dark Mode"
    
    # Animated theme toggle button with CSS
    st.sidebar.markdown(f"""
    <style>
    .theme-toggle {{
        background: none;
        border: none;
        cursor: pointer;
        padding: 8px;
        border-radius: 50%;
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 48px;
        height: 48px;
        margin: 0 auto 16px auto;
        background-color: var(--secondary-bg);
        border: 2px solid var(--border-color);
    }}
    
    .theme-toggle:hover {{
        background-color: var(--tertiary-bg);
        transform: scale(1.1);
        box-shadow: 0 4px 12px var(--shadow-color);
    }}
    
    .sun-and-moon {{
        transition: all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        color: var(--primary-color);
    }}
    
    /* Dark mode state */
    .theme-toggle[data-theme="dark"] .sun {{
        transform: scale(1.75);
    }}
    
    .theme-toggle[data-theme="dark"] .sun-beams {{
        opacity: 0;
        transform: rotateZ(-25deg);
    }}
    
    .theme-toggle[data-theme="dark"] .moon > circle {{
        transform: translateX(-7px);
    }}
    
    /* Light mode state */
    .theme-toggle[data-theme="light"] .sun {{
        transform: scale(1);
    }}
    
    .theme-toggle[data-theme="light"] .sun-beams {{
        opacity: 1;
        transform: rotateZ(0deg);
    }}
    
    .theme-toggle[data-theme="light"] .moon > circle {{
        transform: translateX(0px);
    }}
    
    /* Auto/System mode state */
    .theme-toggle[data-theme="auto"] .sun {{
        transform: scale(1.25);
    }}
    
    .theme-toggle[data-theme="auto"] .sun-beams {{
        opacity: 0.5;
        transform: rotateZ(-12deg);
    }}
    
    .theme-toggle[data-theme="auto"] .moon > circle {{
        transform: translateX(-3px);
    }}
    
    .theme-toggle[data-theme="auto"] {{
        border-color: var(--accent-color);
        background-color: var(--primary-color);
        opacity: 0.8;
    }}
    
    .sun-beams {{
        stroke-width: 2px;
        stroke-linecap: round;
    }}
    
    .theme-label {{
        text-align: center;
        font-size: 0.8rem;
        color: var(--text-secondary);
        margin-top: 4px;
    }}
    </style>
    
    <div style="text-align: center;">
        <button class="theme-toggle" data-theme="{button_state}" title="{tooltip}" onclick="toggleTheme()">
            <svg class="sun-and-moon" aria-hidden="true" width="24" height="24" viewBox="0 0 24 24">
                <mask class="moon" id="moon-mask">
                    <rect x="0" y="0" width="100%" height="100%" fill="white" />
                    <circle cx="24" cy="10" r="6" fill="black" />
                </mask>
                <circle class="sun" cx="12" cy="12" r="6" mask="url(#moon-mask)" fill="currentColor" />
                <g class="sun-beams" stroke="currentColor">
                    <line x1="12" y1="1" x2="12" y2="3" />
                    <line x1="12" y1="21" x2="12" y2="23" />
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                    <line x1="1" y1="12" x2="3" y2="12" />
                    <line x1="21" y1="12" x2="23" y2="12" />
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </g>
            </svg>
        </button>
        <div class="theme-label">{tooltip}</div>
    </div>
    
    <script>
    function toggleTheme() {{
        // This will be handled by Streamlit's rerun mechanism
        window.parent.postMessage({{
            type: 'streamlit:setComponentValue',
            value: '{next_theme}'
        }}, '*');
    }}
    </script>
    """, unsafe_allow_html=True)
    
    # Create invisible button to handle the theme change
    if st.sidebar.button("🔄", key="theme_toggle_hidden", help=f"Switch to {next_theme} mode"):
        st.session_state.theme_override = next_theme
        st.rerun()
    
    st.sidebar.markdown("---")

def apply_kiro_theme_styling():
    """Apply Kiro-inspired theme styling with light/dark mode support"""
    
    # Determine current theme
    current_theme = st.session_state.theme_override
    if current_theme == "system":
        # Let Streamlit handle system detection, but provide fallback
        is_dark = True  # Default fallback
    else:
        is_dark = current_theme == "dark"
    
    # Theme-specific CSS variables
    if is_dark:
        theme_vars = """
        --primary-color: #8B5CF6;
        --background-color: #0F0F23;
        --secondary-bg: #1E1B3A;
        --tertiary-bg: #2D2A4A;
        --text-color: #E5E7EB;
        --text-secondary: #9CA3AF;
        --accent-color: #A855F7;
        --user-msg-bg: #4C1D95;
        --ai-msg-bg: #374151;
        --border-color: #4B5563;
        --shadow-color: rgba(0, 0, 0, 0.4);
        --success-color: #10B981;
        --error-color: #EF4444;
        --warning-color: #F59E0B;
        --info-color: #8B5CF6;
        """
    else:
        theme_vars = """
        --primary-color: #7C3AED;
        --background-color: #FEFEFE;
        --secondary-bg: #F8FAFC;
        --tertiary-bg: #F1F5F9;
        --text-color: #1F2937;
        --text-secondary: #6B7280;
        --accent-color: #8B5CF6;
        --user-msg-bg: #EDE9FE;
        --ai-msg-bg: #F3F4F6;
        --border-color: #D1D5DB;
        --shadow-color: rgba(0, 0, 0, 0.1);
        --success-color: #059669;
        --error-color: #DC2626;
        --warning-color: #D97706;
        --info-color: #7C3AED;
        """
    
    st.markdown(f"""
    <style>
    /* CSS Custom Properties for Kiro-inspired theming */
    :root {{
        {theme_vars}
    }}
    
    /* System theme detection support */
    @media (prefers-color-scheme: dark) {{
        .system-theme:root {{
            --primary-color: #8B5CF6;
            --background-color: #0F0F23;
            --secondary-bg: #1E1B3A;
            --tertiary-bg: #2D2A4A;
            --text-color: #E5E7EB;
            --text-secondary: #9CA3AF;
            --accent-color: #A855F7;
            --user-msg-bg: #4C1D95;
            --ai-msg-bg: #374151;
            --border-color: #4B5563;
            --shadow-color: rgba(0, 0, 0, 0.4);
            --success-color: #10B981;
            --error-color: #EF4444;
            --warning-color: #F59E0B;
            --info-color: #8B5CF6;
        }}
    }}
    
    @media (prefers-color-scheme: light) {{
        .system-theme:root {{
            --primary-color: #7C3AED;
            --background-color: #FEFEFE;
            --secondary-bg: #F8FAFC;
            --tertiary-bg: #F1F5F9;
            --text-color: #1F2937;
            --text-secondary: #6B7280;
            --accent-color: #8B5CF6;
            --user-msg-bg: #EDE9FE;
            --ai-msg-bg: #F3F4F6;
            --border-color: #D1D5DB;
            --shadow-color: rgba(0, 0, 0, 0.1);
            --success-color: #059669;
            --error-color: #DC2626;
            --warning-color: #D97706;
            --info-color: #7C3AED;
        }}
    }}
    
    /* Apply system theme class when needed */
    {"html { }" if current_theme == "system" else ""}
    
    /* Main app styling */
    [data-testid="stAppViewContainer"] {{
        background-color: var(--background-color) !important;
    }}
    
    [data-testid="stHeader"] {{
        background-color: var(--background-color) !important;
    }}
    
    .stApp {{
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
    }}
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {{
        background-color: var(--secondary-bg) !important;
    }}
    
    [data-testid="stSidebar"] .stSelectbox > div > div {{
        background-color: var(--tertiary-bg) !important;
        color: var(--text-color) !important;
        border-color: var(--border-color) !important;
    }}
    
    /* Chat messages */
    [data-testid="stChatMessage"] {{
        background-color: var(--secondary-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        margin: 8px 0 !important;
    }}
    
    [data-testid="stChatMessage"][data-testid*="user"] {{
        background-color: var(--user-msg-bg) !important;
    }}
    
    [data-testid="stChatMessage"][data-testid*="assistant"] {{
        background-color: var(--ai-msg-bg) !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: var(--primary-color) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }}
    
    .stButton > button:hover {{
        background-color: var(--accent-color) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px var(--shadow-color) !important;
    }}
    
    /* Input fields */
    .stTextInput > div > div > input {{
        background-color: var(--tertiary-bg) !important;
        color: var(--text-color) !important;
        border-color: var(--border-color) !important;
    }}
    
    /* Success/Error/Warning messages */
    .stSuccess {{
        background-color: var(--success-color) !important;
        color: white !important;
    }}
    
    .stError {{
        background-color: var(--error-color) !important;
        color: white !important;
    }}
    
    .stWarning {{
        background-color: var(--warning-color) !important;
        color: white !important;
    }}
    
    .stInfo {{
        background-color: var(--info-color) !important;
        color: white !important;
    }}
    
    /* File uploader */
    [data-testid="stFileUploader"] {{
        background-color: var(--secondary-bg) !important;
        border: 2px dashed var(--border-color) !important;
        border-radius: 12px !important;
    }}
    
    /* Progress bars */
    .stProgress > div > div {{
        background-color: var(--primary-color) !important;
    }}
    
    /* Expanders */
    [data-testid="stExpander"] {{
        background-color: var(--secondary-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
    }}
    
    /* Metrics */
    [data-testid="metric-container"] {{
        background-color: var(--secondary-bg) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }}
    
    /* Custom animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .fade-in {{
        animation: fadeIn 0.3s ease-out !important;
    }}
    
    /* Responsive design */
    @media (max-width: 768px) {{
        .stApp {{
            padding: 1rem !important;
        }}
        
        [data-testid="stSidebar"] {{
            width: 100% !important;
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ----------------------------
# Session State Initialization  
# ----------------------------

def clean_message_content(messages):
    """Clean up any corrupted message content"""
    import re
    cleaned_messages = []
    
    for message in messages:
        if isinstance(message, dict) and 'content' in message:
            content = message['content']
            # Remove any HTML div tags that might have been accidentally included
            content = re.sub(r'<div[^>]*>.*?</div>', '', content, flags=re.DOTALL)
            # Clean up any other HTML tags
            content = re.sub(r'<[^>]+>', '', content)
            
            # Create cleaned message
            cleaned_message = message.copy()
            cleaned_message['content'] = content.strip()
            cleaned_messages.append(cleaned_message)
        else:
            cleaned_messages.append(message)
    
    return cleaned_messages

def initialize_session_state():
    """Initialize session state variables with user session isolation"""
    # Generate unique user session ID for privacy
    if 'user_session_id' not in st.session_state:
        import uuid
        st.session_state.user_session_id = str(uuid.uuid4())
    
    if 'model_manager' not in st.session_state:
        st.session_state.model_manager = ModelManager()
    
    # Force refresh of RAGManager if version mismatch (cache issue fix)
    if 'rag_manager' not in st.session_state or not hasattr(st.session_state.rag_manager, 'VERSION'):
        st.session_state.rag_manager = RAGManager()
    
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = SimpleChatbotDB()
    
    if 'conversation_manager' not in st.session_state:
        st.session_state.conversation_manager = ConversationManager(
            st.session_state.rag_manager.db_manager,
            user_session_id=st.session_state.user_session_id
        )
    
    # Clean up any corrupted messages in session state
    if 'messages' in st.session_state:
        st.session_state.messages = clean_message_content(st.session_state.messages)
    
    # Ensure there's always a current conversation
    st.session_state.conversation_manager.ensure_conversation_exists()

# ----------------------------
# UI Components
# ----------------------------
def render_header():
    """Render the application header"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("💬 PharmGPT")
        st.markdown("*Your Pharmacology Assistant*")

def render_conversation_sidebar():
    """Render conversation management in sidebar"""
    st.sidebar.markdown("## 💬 Conversations")
    
    # New conversation button
    if st.sidebar.button("➕ New Conversation", use_container_width=True):
        st.session_state.conversation_manager.create_new_conversation()
        st.rerun()
    
    st.sidebar.markdown("---")

def render_chat_history():
    """Render chat message history using Streamlit's native chat interface"""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

def process_user_message(user_input: str):
    """Process user message and generate AI response with RAG integration"""
    if not user_input.strip():
        return
    
    # Add user message to chat
    st.session_state.conversation_manager.add_message_to_current_conversation(
        role="user",
        content=user_input,
        timestamp=time.time()
    )
    
    # Generate AI response
    try:
        # Get RAG context if available
        context_chunks = []
        try:
            context_chunks = st.session_state.rag_manager.search_documents(
                user_input,
                conversation_id=st.session_state.current_conversation_id,
                user_session_id=st.session_state.user_session_id
            )
        except Exception:
            pass  # Continue without RAG if it fails
        
        # Generate response
        response = st.session_state.model_manager.generate_response(
            message=user_input,
            context_chunks=context_chunks,
            stream=False
        )
        
        # Add AI response to chat
        st.session_state.conversation_manager.add_message_to_current_conversation(
            role="assistant",
            content=response,
            timestamp=time.time(),
            context_used=len(context_chunks) > 0,
            context_chunks=len(context_chunks)
        )
        
    except Exception as e:
        error_response = f"I apologize, but I encountered an error: {str(e)}"
        st.session_state.conversation_manager.add_message_to_current_conversation(
            role="assistant",
            content=error_response,
            timestamp=time.time(),
            error=True
        )

# ----------------------------
# Main Application
# ----------------------------
def main():
    """Main application function with comprehensive error handling and enhanced UI"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Apply Kiro theme styling
        apply_kiro_theme_styling()
        
        # Sidebar components
        render_theme_toggle()
        render_conversation_sidebar()
        
        # Main content
        render_header()
        
        # Document upload
        uploaded_files = st.file_uploader(
            "📄 Upload documents for context",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'md', 'docx'],
            help="Upload documents to enhance AI responses with relevant context"
        )
        
        # Chat interface
        render_chat_history()
        
        # Chat input
        if prompt := st.chat_input("Ask me anything about pharmacology..."):
            with st.chat_message("user"):
                st.write(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    process_user_message(prompt)
                    # Display the latest response
                    if st.session_state.messages:
                        latest_message = st.session_state.messages[-1]
                        if latest_message["role"] == "assistant":
                            st.write(latest_message["content"])
            
            st.rerun()
            
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        if st.button("🔄 Restart Application"):
            st.rerun()

# ----------------------------
# Application Entry Point
# ----------------------------
if __name__ == "__main__":
    main()