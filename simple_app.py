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

def check_conversation_isolation():
    """Check if conversation isolation is working properly"""
    try:
        db = st.session_state.db_manager
        
        if not db.client:
            st.error("❌ No database connection available")
            return
        
        # Check if user_session_id column exists
        try:
            result = db.client.table("document_chunks").select("user_session_id").limit(1).execute()
            schema_updated = True
        except Exception:
            schema_updated = False
        
        if not schema_updated:
            st.error("❌ **CRITICAL: Conversation Isolation Not Working**")
            st.markdown("""
            **🚨 PROBLEM:** Documents uploaded in one conversation are appearing in ALL conversations.
            
            **📋 CAUSE:** Your database schema is missing the `user_session_id` columns needed for proper isolation.
            
            **⚠️ IMPACT:** 
            - Documents leak between conversations
            - Privacy and context mixing issues
            - Incorrect AI responses with wrong context
            
            **✅ SOLUTION:** Run the schema update below in your Supabase database.
            """)
            
            # Show the SQL to run
            try:
                with open('user_session_schema_update.sql', 'r') as f:
                    sql_content = f.read()
                    
                st.markdown("### 🔧 Fix Instructions:")
                st.markdown("""
                1. Go to your **Supabase Dashboard**
                2. Navigate to **SQL Editor**
                3. Create a new query and paste the SQL below
                4. Click **Run** to execute
                5. Restart your Streamlit app
                """)
                
                st.code(sql_content, language='sql')
                
            except FileNotFoundError:
                st.error("❌ user_session_schema_update.sql file not found")
        else:
            # Check for documents with improper isolation
            try:
                result = db.client.table("document_chunks").select("conversation_id, user_session_id, metadata").execute()
                
                if result.data:
                    # Check for documents with default/missing user_session_id
                    anonymous_docs = [doc for doc in result.data if doc.get('user_session_id') in [None, 'anonymous']]
                    total_docs = len(result.data)
                    
                    if anonymous_docs:
                        st.warning(f"⚠️ Found {len(anonymous_docs)} out of {total_docs} documents with default user session")
                        st.info("💡 These documents might appear in multiple conversations. Consider re-uploading them in specific conversations.")
                    else:
                        st.success("✅ All documents have proper conversation isolation!")
                        
                    # Show conversation distribution
                    conversations = {}
                    for doc in result.data:
                        conv_id = doc.get('conversation_id', 'unknown')
                        if conv_id not in conversations:
                            conversations[conv_id] = 0
                        conversations[conv_id] += 1
                    
                    st.markdown("### 📊 Document Distribution by Conversation:")
                    for conv_id, count in conversations.items():
                        st.write(f"- Conversation `{conv_id[:8]}...`: {count} documents")
                    
                    # Show embedding status
                    embedding_status = st.session_state.rag_manager.get_embedding_status()
                    st.markdown("### 🔧 Embedding Model Status:")
                    if embedding_status['model_available']:
                        model_type = "SentenceTransformer" if embedding_status['is_sentence_transformer'] else embedding_status['model_type']
                        st.success(f"✅ {model_type} - {embedding_status['search_method']}")
                    else:
                        st.error(f"❌ {embedding_status['search_method']}")
                        st.info("💡 Fix with: pip install --upgrade sentence-transformers torch")
                        
                else:
                    st.info("📄 No documents found in database")
                    
            except Exception as e:
                st.error(f"❌ Error checking document isolation: {str(e)}")
                
    except Exception as e:
        st.error(f"❌ Error during isolation check: {str(e)}")

def clear_conversation_documents():
    """Clear all documents from the current conversation"""
    try:
        db = st.session_state.db_manager
        
        if not db.client:
            st.error("❌ No database connection available")
            return
        
        # Get current conversation info
        conv_id = st.session_state.current_conversation_id
        user_id = st.session_state.user_session_id
        
        if not conv_id:
            st.error("❌ No active conversation")
            return
        
        # Delete all document chunks for this conversation
        try:
            result = db.client.table("document_chunks").delete().eq("conversation_id", conv_id).eq("user_session_id", user_id).execute()
            
            deleted_count = len(result.data) if result.data else 0
            
            if deleted_count > 0:
                st.success(f"✅ Cleared {deleted_count} document chunks from this conversation")
                
                # Clear the processed files lists
                st.session_state.last_processed_files = []
                if 'conversation_processed_files' in st.session_state:
                    st.session_state.conversation_processed_files[conv_id] = []
                
                # Force a rerun to update the UI
                st.rerun()
            else:
                st.info("📄 No documents found in this conversation")
                
        except Exception as e:
            st.error(f"❌ Error clearing documents: {str(e)}")
            
    except Exception as e:
        st.error(f"❌ Error during document clearing: {str(e)}")

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
        
        # Main content
        render_header()
        
        # Check for schema isolation issue and show warning banner
        try:
            schema_updated = st.session_state.db_manager._check_user_session_schema()
            if not schema_updated:
                st.error("🚨 **CONVERSATION ISOLATION NOT WORKING** - Documents will appear in all conversations until you update your database schema. Click 'Check Conversation Isolation' below for fix instructions.")
        except Exception:
            pass  # Don't break the app if check fails
        
        # Document upload
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
                                # Only show success message and add to processed files if actually successful
                                st.success(f"✅ Processed {uploaded_file.name} → {chunk_count} chunks for this conversation")
                                # Add to conversation-specific processed files
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
            
            # Show document stats only for current conversation
            try:
                stats = st.session_state.rag_manager.get_conversation_document_stats(
                    st.session_state.current_conversation_id,
                    st.session_state.user_session_id
                )
                if stats.get('unique_documents', 0) > 0:
                    st.info(f"📄 {stats['unique_documents']} document(s) ready for context in this conversation")
            except Exception:
                # Fallback to session state if database check fails
                if st.session_state.last_processed_files:
                    st.info(f"📄 {len(st.session_state.last_processed_files)} document(s) ready for context")
            
            # Conversation management buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 Check Conversation Isolation", help="Check if documents are properly isolated between conversations"):
                    check_conversation_isolation()
            with col2:
                if st.button("🗑️ Clear Documents from This Conversation", help="Remove all documents from current conversation"):
                    clear_conversation_documents()
        
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