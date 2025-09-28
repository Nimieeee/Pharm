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

# ----------------------------
# Application Components
# ----------------------------

# Theme toggle function removed - using default Streamlit theme settings

# Kiro theme styling removed - using default Streamlit themes

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

def process_user_message_streaming(user_input: str):
    """Process user message and generate streaming AI response with RAG integration"""
    if not user_input.strip():
        return ""
    
    # Add user message to chat
    st.session_state.conversation_manager.add_message_to_current_conversation(
        role="user",
        content=user_input,
        timestamp=time.time()
    )
    
    # Generate AI response with streaming
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
        
        # Convert context chunks to context string
        context = None
        if context_chunks:
            context = "\n\n".join([chunk.get('content', '') for chunk in context_chunks])
        
        # Generate streaming response
        stream = st.session_state.model_manager.generate_response(
            message=user_input,
            context=context,
            stream=True
        )
        
        # Handle streaming response
        if hasattr(stream, '__iter__'):
            # Stream is iterable (Mistral streaming response)
            full_response = ""
            for chunk in stream:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        full_response += delta.content
                        yield delta.content
            
            # Add complete response to chat after streaming
            if full_response:
                st.session_state.conversation_manager.add_message_to_current_conversation(
                    role="assistant",
                    content=full_response,
                    timestamp=time.time(),
                    context_used=len(context_chunks) > 0,
                    context_chunks=len(context_chunks)
                )
            return full_response
        else:
            # Fallback to non-streaming if stream object is not iterable
            response = str(stream)
            st.session_state.conversation_manager.add_message_to_current_conversation(
                role="assistant",
                content=response,
                timestamp=time.time(),
                context_used=len(context_chunks) > 0,
                context_chunks=len(context_chunks)
            )
            return response
        
    except Exception as e:
        error_response = f"I apologize, but I encountered an error: {str(e)}"
        st.session_state.conversation_manager.add_message_to_current_conversation(
            role="assistant",
            content=error_response,
            timestamp=time.time(),
            error=True
        )
        return error_response

# ----------------------------
# Main Application
# ----------------------------
def main():
    """Main application function with comprehensive error handling and enhanced UI"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Sidebar components
        render_conversation_sidebar()
        
        # Model status check in sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🤖 Model Status")
        try:
            if hasattr(st.session_state, 'model_manager') and st.session_state.model_manager:
                if st.session_state.model_manager.is_model_available():
                    st.sidebar.success("✅ AI Model Ready")
                else:
                    st.sidebar.error("❌ AI Model Not Available")
                    st.sidebar.info("Check MISTRAL_API_KEY")
            else:
                st.sidebar.error("❌ Model Manager Not Initialized")
        except Exception as e:
            st.sidebar.error(f"❌ Model Status Error: {str(e)}")
        
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
                try:
                    # Get RAG context if available
                    context_chunks = []
                    try:
                        context_chunks = st.session_state.rag_manager.search_documents(
                            prompt,
                            conversation_id=st.session_state.current_conversation_id,
                            user_session_id=st.session_state.user_session_id
                        )
                    except Exception:
                        pass  # Continue without RAG if it fails
                    
                    # Convert context chunks to context string
                    context = None
                    if context_chunks:
                        context = "\n\n".join([chunk.get('content', '') for chunk in context_chunks])
                    
                    # Check if model manager is available
                    if not hasattr(st.session_state, 'model_manager') or not st.session_state.model_manager:
                        st.error("❌ Model manager not initialized")
                        return
                    
                    # Check if model is available
                    if not st.session_state.model_manager.is_model_available():
                        st.error("❌ AI model not available. Please check your API key configuration.")
                        st.info("💡 Make sure MISTRAL_API_KEY is set in your environment or Streamlit secrets")
                        return
                    
                    # Try non-streaming first for reliability
                    response = None
                    with st.spinner("Generating response..."):
                        try:
                            response = st.session_state.model_manager.generate_response(
                                message=prompt,
                                context=context,
                                stream=False
                            )
                            
                            # Check if response is valid
                            if not response or not response.strip():
                                st.error("❌ Empty response from AI model")
                                return
                            
                            # Check for API error messages
                            if "API error" in response or "error:" in response.lower():
                                st.error(f"❌ {response}")
                                return
                            
                            # Display the response
                            st.write(response)
                            
                        except Exception as generation_error:
                            st.error(f"❌ Error generating response: {str(generation_error)}")
                            response = f"I apologize, but I encountered an error: {str(generation_error)}"
                            st.write(response)
                    
                    # Add response to conversation if we got one
                    if response and response.strip():
                        st.session_state.conversation_manager.add_message_to_current_conversation(
                            role="assistant",
                            content=response,
                            timestamp=time.time(),
                            context_used=len(context_chunks) > 0,
                            context_chunks=len(context_chunks)
                        )
                    else:
                        # If no response, show error
                        error_response = "I apologize, but I couldn't generate a response. Please try again."
                        st.write(error_response)
                        st.session_state.conversation_manager.add_message_to_current_conversation(
                            role="assistant",
                            content=error_response,
                            timestamp=time.time(),
                            error=True
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