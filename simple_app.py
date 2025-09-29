"""
Simple Chatbot Application
A clean Streamlit chatbot with navigation, homepage, and chat functionality
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import time
import sys
import os

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import our core modules
try:
    import models
    from models import ModelManager
    import rag
    from rag import RAGManager
    from conversation_manager import ConversationManager
    from database import SimpleChatbotDB
except ImportError as e:
    st.error(f"Cannot import required modules: {e}")
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

# ----------------------------
# Session State Initialization  
# ----------------------------
def initialize_session_state():
    """Initialize session state variables with user session isolation"""
    
    # Generate unique user session ID for privacy
    if 'user_session_id' not in st.session_state:
        import uuid
        st.session_state.user_session_id = str(uuid.uuid4())
    
    if 'model_manager' not in st.session_state:
        st.session_state.model_manager = ModelManager()
    
    if 'rag_manager' not in st.session_state:
        st.session_state.rag_manager = RAGManager()
    
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = SimpleChatbotDB()
    
    if 'conversation_manager' not in st.session_state:
        st.session_state.conversation_manager = ConversationManager(
            st.session_state.rag_manager.db_manager,
            user_session_id=st.session_state.user_session_id
        )
    
    # Ensure there's always a current conversation
    st.session_state.conversation_manager.ensure_conversation_exists()

# ----------------------------
# UI Components
# ----------------------------




def render_chat_header():
    """Render the main application header"""
    st.title("🧬 PharmGPT")
    st.markdown("*Your Advanced AI Pharmacology Assistant*")

def render_conversation_sidebar():
    """Render conversation management in sidebar"""
    st.sidebar.markdown("## 💬 Conversations")
    
    # New conversation button
    if st.sidebar.button("➕ New Conversation", use_container_width=True):
        st.session_state.conversation_manager.create_new_conversation()
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Load and display conversations
    try:
        st.session_state.conversation_manager.load_conversations()
        conversations = st.session_state.conversations
        
        if not conversations:
            st.sidebar.info("No conversations yet. Create your first one!")
            return
        
        # Current conversation indicator
        current_id = st.session_state.current_conversation_id
        current_title = st.session_state.conversation_manager.get_current_conversation_title()
        
        st.sidebar.markdown(f"**Current:** {current_title}")
        st.sidebar.markdown("---")
        
        # List all conversations
        for conv in conversations:
            is_current = conv['id'] == current_id
            
            # Create columns for conversation item
            col1, col2 = st.sidebar.columns([3, 1])
            
            with col1:
                # Conversation button
                button_label = f"{'🔵' if is_current else '⚪'} {conv['title']}"
                if st.button(button_label, key=f"conv_{conv['id']}", use_container_width=True):
                    if not is_current:
                        st.session_state.conversation_manager.switch_conversation(conv['id'])
                        st.rerun()
            
            with col2:
                # Delete button (only for non-current conversations or if multiple exist)
                if len(conversations) > 1:
                    if st.button("🗑️", key=f"del_{conv['id']}", help="Delete conversation"):
                        if st.session_state.conversation_manager.delete_conversation(conv['id']):
                            st.rerun()
            
            # Show conversation stats for current conversation
            if is_current:
                try:
                    stats = st.session_state.conversation_manager.get_conversation_stats(conv['id'])
                    st.sidebar.caption(f"📝 {stats.get('message_count', 0)} messages • 📄 {stats.get('document_count', 0)} docs")
                except Exception:
                    pass  # Skip stats if there's an error
                    
    except Exception as e:
        st.sidebar.error(f"Error loading conversations: {str(e)}")
        st.sidebar.info("Using temporary conversation mode")

def render_chat_history():
    """Render chat message history using Streamlit's native chat interface"""
    for message in st.session_state.messages:
        if message["role"] == "assistant":
            with st.chat_message("assistant", avatar="PharmGPT.png"):
                st.write(message["content"])
        else:
            with st.chat_message(message["role"]):
                st.write(message["content"])

# ----------------------------
# Main Application
# ----------------------------
def main():
    """Main application function - direct to chat"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Sidebar components
        render_conversation_sidebar()
        
        # Chat interface
        render_chat_header()
        render_chat_history()
        
        # Document upload
        uploaded_files = st.file_uploader(
            "📄 Upload documents",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'md', 'docx'],
            help="Upload documents to enhance AI responses with relevant context"
        )
        
        # Process uploaded documents
        if uploaded_files:
            with st.spinner("Processing documents..."):
                for uploaded_file in uploaded_files:
                    try:
                        success, chunk_count = st.session_state.rag_manager.process_uploaded_file(
                            uploaded_file,
                            conversation_id=st.session_state.current_conversation_id,
                            user_session_id=st.session_state.user_session_id
                        )
                        if success:
                            st.success(f"✅ Processed {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
        
        # Chat input
        if prompt := st.chat_input("Ask me anything about pharmacology..."):
            # Add user message to chat
            st.session_state.conversation_manager.add_message_to_current_conversation(
                role="user",
                content=prompt,
                timestamp=time.time()
            )
            
            # Display user message
            with st.chat_message("user"):
                st.write(prompt)
            
            # Generate and display assistant response
            with st.chat_message("assistant", avatar="PharmGPT.png"):
                with st.spinner("PharmGPT is thinking..."):
                    try:
                        # Get RAG context if available
                        context = None
                        try:
                            context = st.session_state.rag_manager.get_all_document_context(
                                conversation_id=st.session_state.current_conversation_id,
                                user_session_id=st.session_state.user_session_id
                            )
                        except Exception:
                            context = None
                        
                        # Generate response
                        response = st.session_state.model_manager.generate_response(
                            message=prompt,
                            context=context,
                        )
                        
                        # Display the response
                        st.write(response)
                        
                        # Add response to conversation
                        st.session_state.conversation_manager.add_message_to_current_conversation(
                            role="assistant",
                            content=response,
                            timestamp=time.time(),
                            context_used=bool(context and context.strip()),
                            context_chunks=len(context.split('\n\n')) if context else 0
                        )
                        
                    except Exception as e:
                        error_response = f"I apologize, but I encountered an error: {str(e)}"
                        st.write(error_response)
                        st.session_state.conversation_manager.add_message_to_current_conversation(
                            role="assistant",
                            content=error_response,
                            timestamp=time.time(),
                            error=True
                        )
            
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