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
        # Clear any previous embedding errors to allow retry
        if hasattr(st.session_state, 'embedding_error_shown'):
            del st.session_state.embedding_error_shown
        if hasattr(st.session_state, 'chunk_processing_error_shown'):
            del st.session_state.chunk_processing_error_shown
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
def render_homepage():
    """Render an aesthetic homepage when no messages exist"""
    # Custom CSS for the homepage
    st.markdown("""
    <style>
    .homepage-container {
        text-align: center;
        padding: 2rem 0;
    }
    
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        margin: 2rem 0;
        color: white;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .hero-subtitle {
        font-size: 1.3rem;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin: 1rem;
        border: 1px solid #f0f0f0;
        transition: transform 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #333;
    }
    
    .feature-description {
        color: #666;
        line-height: 1.6;
    }
    
    .stats-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
    }
    
    .stat-item {
        text-align: center;
        padding: 1rem;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
    }
    
    .stat-label {
        color: #666;
        font-weight: 500;
    }
    
    .cta-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        color: white;
    }
    
    .quick-start-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 2rem 0;
    }
    
    .quick-start-item {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .quick-start-number {
        background: #667eea;
        color: white;
        width: 30px;
        height: 30px;
        border-radius: 50%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-right: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="homepage-container">
        <div class="hero-section">
            <div class="hero-title">🧬 PharmGPT</div>
            <div class="hero-subtitle">Your Advanced AI Pharmacology Assistant</div>
            <p style="font-size: 1.1rem; opacity: 0.8; max-width: 600px; margin: 0 auto;">
                Harness the power of AI to explore pharmacology, drug interactions, mechanisms of action, 
                and clinical applications with intelligent document analysis and expert-level insights.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Features Section
    st.markdown("## ✨ Key Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <div class="feature-title">AI-Powered Analysis</div>
            <div class="feature-description">
                Advanced language models trained on pharmacological data provide accurate, 
                contextual responses to complex drug-related queries.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">📚</div>
            <div class="feature-title">Document Intelligence</div>
            <div class="feature-description">
                Upload research papers, drug monographs, and clinical guidelines. 
                PharmGPT extracts and synthesizes relevant information instantly.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <div class="feature-icon">💬</div>
            <div class="feature-title">Conversational Interface</div>
            <div class="feature-description">
                Natural language conversations with context awareness. 
                Ask follow-up questions and build on previous discussions.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick Start Guide
    st.markdown("## 🚀 Quick Start Guide")
    
    st.markdown("""
    <div class="quick-start-grid">
        <div class="quick-start-item">
            <span class="quick-start-number">1</span>
            <strong>Ask Questions</strong><br>
            Type your pharmacology questions in the chat below
        </div>
        <div class="quick-start-item">
            <span class="quick-start-number">2</span>
            <strong>Upload Documents</strong><br>
            Add PDFs, research papers, or drug information files
        </div>
        <div class="quick-start-item">
            <span class="quick-start-number">3</span>
            <strong>Get Insights</strong><br>
            Receive AI-powered analysis with document context
        </div>
        <div class="quick-start-item">
            <span class="quick-start-number">4</span>
            <strong>Manage Conversations</strong><br>
            Create multiple conversations for different topics
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Example Questions
    st.markdown("## 💡 Example Questions to Get Started")
    
    example_questions = [
        "What is the mechanism of action of ACE inhibitors?",
        "Explain the pharmacokinetics of warfarin and its drug interactions",
        "Compare the efficacy of different beta-blockers in heart failure",
        "What are the contraindications for NSAIDs in elderly patients?",
        "Describe the MOA of novel diabetes medications like GLP-1 agonists"
    ]
    
    for i, question in enumerate(example_questions, 1):
        st.markdown(f"**{i}.** {question}")
    
    # Call to Action
    st.markdown("""
    <div class="cta-section">
        <h3 style="margin-top: 0;">Ready to explore pharmacology with AI?</h3>
        <p style="font-size: 1.1rem; margin-bottom: 0;">
            Start by typing a question in the chat input below, or upload a document to begin your analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_header():
    """Render the application header"""
    # Only show minimal header when there are messages
    if st.session_state.messages:
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
        
        # Main content - show homepage if no messages, otherwise show chat
        if not st.session_state.messages:
            render_homepage()
        else:
            render_header()
            
            # Check for schema isolation issue and show warning banner
            try:
                schema_updated = st.session_state.db_manager._check_user_session_schema()
                if not schema_updated:
                    st.error("🚨 **CONVERSATION ISOLATION NOT WORKING** - Documents will appear in all conversations until you update your database schema. Click 'Check Conversation Isolation' below for fix instructions.")
            except Exception:
                pass  # Don't break the app if check fails
            
            # Chat interface
            render_chat_history()
        
        # Document upload (above chat input)
        uploaded_files = st.file_uploader(
            "📄 Upload documents",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'md', 'docx'],
            help="Upload documents to enhance AI responses with relevant context"
        )
        
        # Process uploaded documents
        if uploaded_files:
            # Check if these are new files for this conversation
            current_files = [f.name for f in uploaded_files]
            if 'last_processed_files' not in st.session_state:
                st.session_state.last_processed_files = []
            
            # Get conversation-specific processed files
            conv_id = st.session_state.current_conversation_id
            if 'conversation_processed_files' not in st.session_state:
                st.session_state.conversation_processed_files = {}
            
            conv_processed_files = st.session_state.conversation_processed_files.get(conv_id, [])
            
            # Check against both session and conversation-specific files
            all_processed = set(st.session_state.last_processed_files + conv_processed_files)
            new_files = [f for f in uploaded_files if f.name not in all_processed]
            
            if new_files:
                # Simple but visible loading indicator for document processing
                progress_placeholder = st.empty()
                progress_placeholder.markdown(f"""
                <div style="text-align: center; padding: 20px;">
                    <div class="simple-loader"></div>
                    <p style="margin-top: 20px; color: #666; font-weight: 500;">Processing {len(new_files)} document(s)...</p>
                </div>
                <style>
                .simple-loader {{
                    width: 40px;
                    height: 40px;
                    margin: 0 auto;
                    border: 4px solid #f3f3f3;
                    border-top: 4px solid #8B5CF6;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
                </style>
                """, unsafe_allow_html=True)
                
                try:
                    for uploaded_file in new_files:
                        try:
                            # Basic file validation
                            if uploaded_file.size > 50 * 1024 * 1024:  # 50MB limit
                                st.warning(f"⚠️ File {uploaded_file.name} is too large (>50MB)")
                                continue
                            
                            if uploaded_file.size == 0:
                                st.warning(f"⚠️ File {uploaded_file.name} is empty")
                                continue
                            
                            # Process the file
                            success, chunk_count = st.session_state.rag_manager.process_uploaded_file(
                                uploaded_file,
                                conversation_id=st.session_state.current_conversation_id,
                                user_session_id=st.session_state.user_session_id
                            )
                            
                            if success and chunk_count > 0:
                                # Add to conversation-specific processed files (no success message)
                                if 'conversation_processed_files' not in st.session_state:
                                    st.session_state.conversation_processed_files = {}
                                conv_id = st.session_state.current_conversation_id
                                if conv_id not in st.session_state.conversation_processed_files:
                                    st.session_state.conversation_processed_files[conv_id] = []
                                st.session_state.conversation_processed_files[conv_id].append(uploaded_file.name)
                                # Also update the legacy list for backward compatibility
                                if uploaded_file.name not in st.session_state.last_processed_files:
                                    st.session_state.last_processed_files.append(uploaded_file.name)
                            else:
                                st.error(f"❌ Failed to process {uploaded_file.name}")
                                
                        except Exception as e:
                            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
            
                finally:
                    # Clear the progress indicator
                    progress_placeholder.empty()
        
        # Document processing happens silently in background
        
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
                    context = None
                    try:
                        # Get ALL document content for unlimited context
                        context = st.session_state.rag_manager.get_all_document_context(
                            conversation_id=st.session_state.current_conversation_id,
                            user_session_id=st.session_state.user_session_id
                        )
                    except Exception as e:
                        context = None
                    
                    # Check if model manager is available
                    if not hasattr(st.session_state, 'model_manager') or not st.session_state.model_manager:
                        st.error("❌ Model manager not initialized")
                        return
                    
                    # Check if model is available
                    if not st.session_state.model_manager.is_model_available():
                        st.error("❌ AI model not available. Please check your API key configuration.")
                        st.info("💡 Make sure MISTRAL_API_KEY is set in your environment or Streamlit secrets")
                        return
                    
                    # Generate response (non-streaming for reliability)
                    response = None
                    
                    # Show loading indicator for AI response
                    thinking_placeholder = st.empty()
                    thinking_placeholder.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <div class="ai-simple-loader"></div>
                        <p style="margin-top: 20px; color: #666; font-weight: 500;">PharmGPT is thinking...</p>
                    </div>
                    <style>
                    .ai-simple-loader {
                        width: 40px;
                        height: 40px;
                        margin: 0 auto;
                        border: 4px solid #f3f3f3;
                        border-top: 4px solid #A855F7;
                        border-radius: 50%;
                        animation: ai-spin 1s linear infinite;
                    }
                    @keyframes ai-spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Add a small delay to ensure spinner is visible
                    time.sleep(0.5)
                    
                    try:
                        response = st.session_state.model_manager.generate_response(
                            message=prompt,
                            context=context,
                            stream=False
                        )
                        
                        # Validate response
                        if not response:
                            st.error("❌ No response from AI model (None)")
                            return
                        
                        if not str(response).strip():
                            st.error("❌ Empty response from AI model (empty string)")
                            return
                        
                        # Check for API error messages
                        response_str = str(response)
                        if "API error" in response_str or "error:" in response_str.lower():
                            st.error(f"❌ API Error: {response_str}")
                            return
                        
                        # Display the response
                        st.write(response_str)
                        response = response_str
                        
                    except Exception as generation_error:
                        st.error(f"❌ Error generating response: {str(generation_error)}")
                        response = f"I apologize, but I encountered an error: {str(generation_error)}"
                        st.write(response)
                    
                    finally:
                        # Ensure spinner is visible for at least 1 second total
                        time.sleep(0.5)
                        # Clear the thinking indicator
                        thinking_placeholder.empty()
                    
                    # Add response to conversation if we got one
                    if response and response.strip():
                        st.session_state.conversation_manager.add_message_to_current_conversation(
                            role="assistant",
                            content=response,
                            timestamp=time.time(),
                            context_used=bool(context and context.strip()),
                            context_chunks=len(context.split('\n\n')) if context else 0
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