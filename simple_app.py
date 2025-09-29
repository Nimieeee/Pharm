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
    # Initialize current view (homepage or chat)
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'homepage'
    
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
def render_navigation():
    """Render navigation bar"""
    st.markdown("""
    <style>
    .nav-container {
        background: white;
        padding: 1rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("🏠 Home", use_container_width=True, 
                    type="primary" if st.session_state.current_view == 'homepage' else "secondary"):
            st.session_state.current_view = 'homepage'
            st.rerun()
    
    with col2:
        st.markdown("<div style='text-align: center; padding: 0.5rem;'><h3>🧬 PharmGPT</h3></div>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("💬 Chat", use_container_width=True,
                    type="primary" if st.session_state.current_view == 'chat' else "secondary"):
            st.session_state.current_view = 'chat'
            st.rerun()

def render_homepage():
    """Render an aesthetic homepage"""
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
            <strong>Navigate to Chat</strong><br>
            Click the "Chat" button in the navigation above
        </div>
        <div class="quick-start-item">
            <span class="quick-start-number">2</span>
            <strong>Upload Documents</strong><br>
            Add PDFs, research papers, or drug information files
        </div>
        <div class="quick-start-item">
            <span class="quick-start-number">3</span>
            <strong>Ask Questions</strong><br>
            Type your pharmacology questions in the chat
        </div>
        <div class="quick-start-item">
            <span class="quick-start-number">4</span>
            <strong>Get Insights</strong><br>
            Receive AI-powered analysis with document context
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
        <p style="font-size: 1.1rem; margin-bottom: 1.5rem;">
            Click the "Chat" button above to start your conversation with PharmGPT.
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_chat_header():
    """Render the chat page header"""
    st.title("💬 PharmGPT Chat")
    st.markdown("*Ask me anything about pharmacology...*")

def render_conversation_sidebar():
    """Render conversation management in sidebar - only show in chat view"""
    if st.session_state.current_view != 'chat':
        return
        
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
    """Main application function with navigation"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Navigation
        render_navigation()
        
        # Sidebar components (only for chat view)
        render_conversation_sidebar()
        
        # Main content based on current view
        if st.session_state.current_view == 'homepage':
            render_homepage()
            
        elif st.session_state.current_view == 'chat':
            render_chat_header()
            
            # Chat interface
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
                                stream=False
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