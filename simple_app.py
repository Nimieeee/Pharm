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

try:
    from models import ModelManager
except ImportError as e:
    st.error(f"Cannot import ModelManager: {e}")
    st.stop()

try:
    from rag import RAGManager
except ImportError as e:
    st.error(f"Cannot import RAGManager: {e}")
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
    page_title="💬 Simple Chatbot",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------
# Dark Mode Styling
# ----------------------------
def apply_dark_mode_styling():
    """Apply comprehensive dark mode styling across the application with enhanced error handling"""
    st.markdown("""
    <style>
    /* CSS Custom Properties for consistent theming */
    :root {
        --primary-color: #4fc3f7;
        --background-color: #0e1117;
        --secondary-bg: #262730;
        --text-color: #ffffff;
        --accent-color: #ff6b6b;
        --user-msg-bg: #1e3a8a;
        --ai-msg-bg: #374151;
        --border-color: #4b5563;
        --shadow-color: rgba(0, 0, 0, 0.4);
        --success-color: #10b981;
        --error-color: #ef4444;
        --warning-color: #f59e0b;
        --info-color: #3b82f6;
    }
    
    /* Main app background with enhanced contrast */
    .stApp {
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    /* Sidebar styling with improved visibility */
    .css-1d391kg {
        background-color: var(--secondary-bg) !important;
        color: var(--text-color) !important;
        border-right: 1px solid var(--border-color);
    }
    
    /* Enhanced chat message containers */
    .chat-message {
        padding: 1rem 1.25rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid;
        box-shadow: 0 2px 8px var(--shadow-color);
        animation: slideIn 0.3s ease-out;
        word-wrap: break-word;
        max-width: 85%;
    }
    
    .user-message {
        background: linear-gradient(135deg, var(--user-msg-bg), color-mix(in srgb, var(--user-msg-bg) 90%, white));
        border-left-color: var(--primary-color);
        margin-left: auto;
        margin-right: 0;
        text-align: right;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, var(--ai-msg-bg), color-mix(in srgb, var(--ai-msg-bg) 95%, white));
        border-left-color: var(--success-color);
        margin-left: 0;
        margin-right: auto;
    }
    
    .error-message {
        background: linear-gradient(135deg, color-mix(in srgb, var(--error-color) 20%, var(--secondary-bg)), var(--secondary-bg));
        border-left-color: var(--error-color);
        color: var(--text-color) !important;
    }
    
    .system-message {
        background: linear-gradient(135deg, color-mix(in srgb, var(--warning-color) 20%, var(--secondary-bg)), var(--secondary-bg));
        border-left-color: var(--warning-color);
        text-align: center;
        font-style: italic;
        margin: 0.5rem auto;
        max-width: 70%;
    }
    
    /* Enhanced input styling with focus states */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: var(--secondary-bg) !important;
        color: var(--text-color) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 0.75rem !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary-color) 20%, transparent) !important;
        outline: none !important;
    }
    
    /* Enhanced button styling with hover effects */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color), color-mix(in srgb, var(--primary-color) 80%, black)) !important;
        color: white !important;
        border: none !important;
        border-radius: 0.75rem !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, var(--accent-color), color-mix(in srgb, var(--accent-color) 80%, black)) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px var(--shadow-color) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Enhanced model toggle styling */
    .model-toggle {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem;
        background: linear-gradient(135deg, var(--secondary-bg), color-mix(in srgb, var(--secondary-bg) 95%, white));
        border: 1px solid var(--border-color);
        border-radius: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px var(--shadow-color);
    }
    
    /* Toggle Switch Styling */
    .toggle-switch-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    padding: 0.75rem;
        background: var(--secondary-bg);
        border-radius: 0.75rem;
        border: 1px solid var(--border-color);
        margin: 0.5rem 0;
    }
    
    .toggle-switch {
        position: relative;
        disp
        width: 60px;
        height: 30px;
        cursor: pointer;
    }
    
    .toggle-switch input {
        opacity: 0;
        width: 0;
     0;
    }
    
    .toggle-slider {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        backgroundgradient(135deg, #6c757d, #495057);
        border-radius: 30px;
        transition: all 0.3s ease;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
    }
    
    .toggle-slider:before {
        position: absolute;
        content: "";
    ight: 24px;
    width: 24px;
        left: 3px;
        bottom: 3px;
        background: linear-gradient(1, #ffffff, #f8f9fa);
        border-radius: 50
    /* Etransition: all 0.3s ease;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    }
  nhanced file uploader styling */
    .toggle-switch input:checked + .toggle-slider {
        background: linear-gradient(135deg, var(--primary-color), color-mix(in srgb, var(--primary-color) 80%, #000)  .stFileUploader > div {
        background-color: var(--secondary-bg) !important;
        border: 2px dashed var(--border-color) !important;
    .toggle-switch input:checked + .toggle-slider:before {
        transform: translateX(30px);
        background: linear-gradient(135deg, #ffffff, #f0f8ff);
    }
    
    .toggle     ch:hover booggle-slider {
     rder-radiadow: inset 0 2px 4px rgba(0,0,0,0.2), 0 0 8px rgba(79, 195, 247, 0.3);
    }
    
    .toggle-labus: 1rem !important;
        paddiweight: 500;
        font-size: 0.9rem;
        transition: all 0.3s ease;
        min-width: 60px;
        text-align: center;
    }
    
   ng: 2rem !important;e {
        color: var(--primary-color);
        font-weight: 600;
        transform: scale(1.05);
    }
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader > div:hover {
        border-color: var(--primary-color) !important;
        background-color: color-mix(in srgb, var(--primary-color) 5%, var(--secondary-bg)) !important;
    }
    
    /* Enhanced alert styling with better contrast */
    .stSuccess {
        background-color: color-mix(in srgb, var(--success-color) 20%, var(--secondary-bg)) !important;
        color: var(--text-color) !important;
        border-left: 4px solid var(--success-color) !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    .stError {
        background-color: color-mix(in srgb, var(--error-color) 20%, var(--secondary-bg)) !important;
        color: var(--text-color) !important;
        border-left: 4px solid var(--error-color) !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    .stWarning {
        background-color: color-mix(in srgb, var(--warning-color) 20%, var(--secondary-bg)) !important;
        color: var(--text-color) !important;
        border-left: 4px solid var(--warning-color) !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    .stInfo {
        background-color: color-mix(in srgb, var(--info-color) 20%, var(--secondary-bg)) !important;
        color: var(--text-color) !important;
        border-left: 4px solid var(--info-color) !important;
        border-radius: 0.5rem !important;
        padding: 1rem !important;
    }
    
    /* Enhanced selectbox and form elements */
    .stSelectbox > div > div > select,
    .stMultiSelect > div > div > div,
    .stNumberInput > div > div > input {
        background-color: var(--secondary-bg) !important;
        color: var(--text-color) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 0.5rem !important;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background-color: var(--primary-color) !important;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: var(--primary-color) !important;
    }
    
    /* Enhanced animations */
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Status indicators */
    .status-indicator {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.5rem 0;
    }
    
    .status-online {
        background-color: color-mix(in srgb, var(--success-color) 20%, transparent);
        color: var(--success-color);
        border: 1px solid color-mix(in srgb, var(--success-color) 40%, transparent);
    }
    
    .status-offline {
        background-color: color-mix(in srgb, var(--error-color) 20%, transparent);
        color: var(--error-color);
        border: 1px solid color-mix(in srgb, var(--error-color) 40%, transparent);
    }
    
    .status-loading {
        background-color: color-mix(in srgb, var(--warning-color) 20%, transparent);
        color: var(--warning-color);
        border: 1px solid color-mix(in srgb, var(--warning-color) 40%, transparent);
    }
    
    .status-dot {
        width: 0.5rem;
        height: 0.5rem;
        border-radius: 50%;
        background-color: currentColor;
    }
    
    .status-loading .status-dot {
        animation: pulse 1s infinite;
    }
    
    /* Enhanced responsive design */
    @media (max-width: 1024px) {
        .chat-message {
            max-width: 90%;
            padding: 1rem;
        }
    }
    
    @media (max-width: 768px) {
        .stApp {
            padding: 0.5rem !important;
        }
        
        .chat-message {
            max-width: 95%;
            margin: 0.75rem 0;
            padding: 0.875rem 1rem;
            font-size: 0.9rem;
        }
        
        .user-message {
            margin-left: 1rem;
        }
        
        .assistant-message {
            margin-right: 1rem;
        }
        
        .main .block-container {
            padding-top: 1rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        .model-toggle {
            padding: 0.75rem;
            margin: 0.75rem 0;
        }
        
        .stButton > button {
            padding: 0.625rem 1rem !important;
            font-size: 0.875rem !important;
        }
    }
    
    @media (max-width: 480px) {
        .chat-message {
            max-width: 100%;
            margin: 0.5rem 0;
            padding: 0.75rem;
            font-size: 0.875rem;
        }
        
        .user-message {
            margin-left: 0.5rem;
        }
        
        .assistant-message {
            margin-right: 0.5rem;
        }
        
        .stTextInput > div > div > input {
            font-size: 16px !important; /* Prevent zoom on iOS */
            padding: 0.625rem 0.875rem !important;
        }
        
        /* Stack columns on mobile */
        .stColumns > div {
            min-width: 100% !important;
            margin-bottom: 0.5rem;
        }
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        .chat-message {
            border: 2px solid;
        }
        
        .user-message {
            border-color: var(--primary-color);
        }
        
        .assistant-message {
            border-color: var(--success-color);
        }
        
        .stButton > button {
            border: 2px solid currentColor;
        }
    }
    
    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        .chat-message {
            animation: none;
        }
        
        .stButton > button {
            transition: none !important;
        }
        
        .status-loading .status-dot {
            animation: none;
        }
    }
    
    /* Focus indicators for accessibility */
    *:focus {
        outline: 2px solid var(--primary-color) !important;
        outline-offset: 2px !important;
    }
    
    /* Ensure all text elements have proper contrast */
    .stMarkdown, .stText, p, span, div, label {
        color: var(--text-color) !important;
    }
    
    /* High contrast for links */
    a {
        color: var(--primary-color) !important;
    }
    
    a:hover {
        color: var(--accent-color) !important;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--secondary-bg);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-color);
    }
    </style>
    """, unsafe_allow_html=True)

# ----------------------------
# Session State Initialization
# ----------------------------
def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'model_manager' not in st.session_state:
        st.session_state.model_manager = ModelManager()
    
    if 'rag_manager' not in st.session_state:
        st.session_state.rag_manager = RAGManager()
    
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = SimpleChatbotDB()
    


# ----------------------------
# UI Components
# ----------------------------
def render_header():
    """Render the application header"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("💬 PharmGPT")
        st.markdown("*Advanced Pharmacology Assistant powered by Mistral AI*")
    
    with col2:
        # Connection status indicator
        if st.session_state.model_manager.is_model_available():
            st.markdown("🟢 **Mistral Ready**")
        else:
            st.markdown("🔴 **API Key Required**")



def render_document_upload_inline():
    """Render document upload interface above chat input with auto-processing"""
    st.markdown("### 📚 Document Upload")
    
    # Document upload section - inline above chat
    uploaded_files = st.file_uploader(
        "Upload documents to enhance chat responses",
        accept_multiple_files=True,
        type=['pdf', 'txt', 'md', 'docx'],
        help="Upload PDF, TXT, MD, or DOCX files. They will be processed automatically.",
        key="document_uploader_inline"
    )
    
    # Auto-process uploaded files
    if uploaded_files:
        # Check if these are new files
        current_files = [f.name for f in uploaded_files]
        if 'last_processed_files' not in st.session_state:
            st.session_state.last_processed_files = []
        
        new_files = [f for f in uploaded_files if f.name not in st.session_state.last_processed_files]
        
        if new_files:
            st.info(f"🔄 Auto-processing {len(new_files)} new document(s)...")
            
            # Process new files automatically with detailed error handling
            success_count = 0
            for uploaded_file in new_files:
                try:
                    # Validate file first
                    if uploaded_file.size > 10 * 1024 * 1024:  # 10MB limit
                        st.error(f"❌ {uploaded_file.name}: File too large (max 10MB)")
                        continue
                    
                    if uploaded_file.size == 0:
                        st.error(f"❌ {uploaded_file.name}: File is empty")
                        continue
                    
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        # Check if RAG manager is properly initialized
                        if not hasattr(st.session_state, 'rag_manager') or not st.session_state.rag_manager:
                            st.error("❌ RAG system not initialized. Please refresh the page.")
                            break
                        
                        # Check if embedding model is available
                        if not st.session_state.rag_manager.embedding_model:
                            st.error("❌ Embedding model not available. Please check your configuration.")
                            break
                        
                        # Check database connection
                        if not st.session_state.rag_manager.db_manager.is_connected():
                            st.error("❌ Database not connected. Please check your Supabase configuration.")
                            break
                        
                        success, chunk_count = st.session_state.rag_manager.process_uploaded_file(
                            uploaded_file, 
                            progress_callback=lambda msg: st.info(f"🔄 {msg}")
                        )
                        
                        if success and chunk_count > 0:
                            success_count += 1
                            st.success(f"✅ {uploaded_file.name}: {chunk_count} chunks processed")
                        else:
                            st.error(f"❌ {uploaded_file.name}: Processing failed - no chunks created")
                            
                except Exception as e:
                    error_msg = str(e)
                    if "embedding" in error_msg.lower():
                        st.error(f"❌ {uploaded_file.name}: Embedding generation failed. Check your API keys.")
                    elif "database" in error_msg.lower():
                        st.error(f"❌ {uploaded_file.name}: Database error. Check your Supabase connection.")
                    elif "document" in error_msg.lower():
                        st.error(f"❌ {uploaded_file.name}: Document format error. Try a different file.")
                    else:
                        st.error(f"❌ {uploaded_file.name}: {error_msg}")
            
            # Update processed files list only for successful files
            if success_count > 0:
                successful_files = [f.name for f in new_files[:success_count]]
                st.session_state.last_processed_files.extend(successful_files)
                st.success(f"🎉 Successfully processed {success_count} document(s)!")
            else:
                st.warning("⚠️ No documents were processed successfully. Please check your configuration.")
    
    # Show current document status and system health
    try:
        stats = st.session_state.rag_manager.get_document_stats()
        if stats['total_chunks'] > 0:
            st.info(f"📚 **{stats['total_chunks']} document chunks** ready for search")
        
        # System health check
        if st.button("🔍 Check System Status", help="Check if all systems are working"):
            with st.expander("System Status", expanded=True):
                # Check RAG manager
                if hasattr(st.session_state, 'rag_manager') and st.session_state.rag_manager:
                    st.success("✅ RAG Manager: Initialized")
                    
                    # Check embedding model
                    if st.session_state.rag_manager.embedding_model:
                        st.success("✅ Embedding Model: Available")
                    else:
                        st.error("❌ Embedding Model: Not available")
                        st.info("💡 Install sentence-transformers or set OPENAI_API_KEY")
                    
                    # Check database
                    if st.session_state.rag_manager.db_manager.is_connected():
                        st.success("✅ Database: Connected")
                        
                        # Test database schema
                        if st.session_state.rag_manager.db_manager.check_schema_exists():
                            st.success("✅ Database Schema: Ready")
                        else:
                            st.error("❌ Database Schema: Missing")
                            st.info("💡 Run the SQL schema from simple_chatbot_schema.sql")
                    else:
                        st.error("❌ Database: Not connected")
                        st.info("💡 Check your Supabase URL and API key")
                else:
                    st.error("❌ RAG Manager: Not initialized")
    
    except Exception as e:
        st.error(f"Error checking document status: {str(e)}")
    
    return uploaded_files

def render_document_upload():
    """Simplified sidebar - no document status shown"""
    # Document upload is now inline, no sidebar content needed
    # This function is kept for compatibility but does nothing
    return None
    
    # Processing options
    if uploaded_files:
        st.sidebar.markdown("**Processing Options:**")
        
        # Chunk size configuration
        chunk_size = st.sidebar.slider(
            "Chunk Size",
            min_value=200,
            max_value=2000,
            value=1000,
            step=100,
            help="Size of text chunks for processing"
        )
        
        chunk_overlap = st.sidebar.slider(
            "Chunk Overlap",
            min_value=0,
            max_value=500,
            value=200,
            step=50,
            help="Overlap between consecutive chunks"
        )
        
        # Auto-process toggle
        auto_process = st.sidebar.checkbox(
            "Auto-process on upload",
            value=False,
            help="Automatically process files when uploaded"
        )
        
        # Process button or auto-processing
        if auto_process:
            if 'last_uploaded_files' not in st.session_state or st.session_state.last_uploaded_files != [f.name for f in uploaded_files]:
                st.session_state.last_uploaded_files = [f.name for f in uploaded_files]
                process_uploaded_documents(uploaded_files, chunk_size, chunk_overlap)
        else:
            if st.sidebar.button("🔄 Process Documents", type="primary", key="process_docs_btn"):
                process_uploaded_documents(uploaded_files, chunk_size, chunk_overlap)
    
    # Document management section
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Document Management:**")
    
    # Display enhanced document stats
    stats = st.session_state.rag_manager.get_document_stats()
    if stats['total_chunks'] > 0:
        st.sidebar.success(f"📄 {stats['total_chunks']} chunks from {stats['unique_documents']} documents")
        
        # Show detailed stats in expander
        with st.sidebar.expander("📊 Document Details", expanded=False):
            st.markdown(f"""
            **Storage Info:**
            - 📁 Unique documents: {stats['unique_documents']}
            - 📄 Total chunks: {stats['total_chunks']}
            - 💾 Storage size: {stats['total_size_mb']} MB
            - 🧠 Embedding model: {stats['embedding_model']}
            - 🕒 Last updated: {stats['last_updated'][:19] if stats['last_updated'] != 'Never' else 'Never'}
            """)
        
        # Clear documents option with confirmation
        if st.sidebar.button("🗑️ Clear All Documents", help="Remove all stored document chunks"):
            if 'confirm_clear' not in st.session_state:
                st.session_state.confirm_clear = True
                st.sidebar.warning("⚠️ This will delete all documents!")
                if st.sidebar.button("✅ Confirm Clear", type="primary"):
                    if clear_all_documents():
                        st.sidebar.success("All documents cleared!")
                        del st.session_state.confirm_clear
                        st.rerun()
                if st.sidebar.button("❌ Cancel"):
                    del st.session_state.confirm_clear
                    st.rerun()
    else:
        st.sidebar.info("No documents uploaded yet")
        st.sidebar.markdown("*Upload PDF, TXT, MD, or DOCX files to get started*")
    
    # Processing status display
    if 'processing_status' in st.session_state:
        status = st.session_state.processing_status
        if status['active']:
            progress = status.get('progress', 0)
            current_file = status.get('current_file', '')
            st.sidebar.progress(progress)
            st.sidebar.text(f"Processing: {current_file}")
        else:
            # Clear completed status after a delay
            if status.get('completed_time', 0) + 5 < time.time():
                del st.session_state.processing_status

def handle_document_processing_error(error: Exception, filename: str) -> dict:
    """Handle document processing errors with specific guidance"""
    error_str = str(error).lower()
    
    if "size" in error_str or "large" in error_str:
        return {
            'type': 'size_error',
            'message': f"📄 **File Too Large: {filename}**\n\nThe file exceeds the maximum size limit (10MB).",
            'suggestions': [
                "Try splitting large documents into smaller parts",
                "Compress the file or reduce image quality",
                "Use a different file format (e.g., TXT instead of PDF)"
            ],
            'recoverable': True
        }
    elif "format" in error_str or "type" in error_str or "unsupported" in error_str:
        return {
            'type': 'format_error',
            'message': f"📄 **Unsupported Format: {filename}**\n\nThis file type is not supported for processing.",
            'suggestions': [
                "Supported formats: PDF, DOCX, TXT, MD",
                "Convert your file to a supported format",
                "Try copying text content to a TXT file"
            ],
            'recoverable': True
        }
    elif "corrupt" in error_str or "damaged" in error_str:
        return {
            'type': 'corruption_error',
            'message': f"📄 **File Corrupted: {filename}**\n\nThe file appears to be damaged or corrupted.",
            'suggestions': [
                "Try re-downloading or re-saving the file",
                "Open the file in its native application and save again",
                "Use a different copy of the document"
            ],
            'recoverable': True
        }
    elif "permission" in error_str or "access" in error_str:
        return {
            'type': 'permission_error',
            'message': f"📄 **Access Denied: {filename}**\n\nUnable to access the file due to permission restrictions.",
            'suggestions': [
                "Check if the file is password-protected",
                "Ensure the file is not open in another application",
                "Try uploading from a different location"
            ],
            'recoverable': True
        }
    elif "network" in error_str or "connection" in error_str:
        return {
            'type': 'network_error',
            'message': f"📄 **Upload Failed: {filename}**\n\nNetwork connection issue during file upload.",
            'suggestions': [
                "Check your internet connection",
                "Try uploading again",
                "Refresh the page and retry"
            ],
            'recoverable': True
        }
    else:
        return {
            'type': 'unknown_error',
            'message': f"📄 **Processing Error: {filename}**\n\nUnexpected error: {str(error)}",
            'suggestions': [
                "Try uploading the file again",
                "Check if the file opens correctly on your device",
                "Contact support if the issue persists"
            ],
            'recoverable': True
        }

def display_document_error_summary(error_info: dict, filename: str):
    """Display document processing error with recovery options"""
    st.error(error_info['message'])
    
    if error_info['suggestions']:
        with st.expander("💡 **Troubleshooting Tips**", expanded=True):
            for suggestion in error_info['suggestions']:
                st.markdown(f"• {suggestion}")
    
    if error_info['recoverable']:
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"🔄 Retry {filename}", key=f"retry_{filename}_{time.time()}"):
                # Clear the file from failed list and allow retry
                if 'failed_files_retry' not in st.session_state:
                    st.session_state.failed_files_retry = []
                st.session_state.failed_files_retry.append(filename)
                st.rerun()
        
        with col2:
            if st.button("📄 Choose Different File", key=f"choose_different_{time.time()}"):
                # Clear file uploader
                if 'document_uploader' in st.session_state:
                    del st.session_state.document_uploader
                st.rerun()

def process_uploaded_documents(uploaded_files, chunk_size=1000, chunk_overlap=200):
    """Enhanced document processing with comprehensive error handling and recovery"""
    if not uploaded_files:
        return
    
    # Initialize processing status
    st.session_state.processing_status = {
        'active': True,
        'progress': 0,
        'current_file': '',
        'total_files': len(uploaded_files),
        'processed_files': 0,
        'failed_files': [],
        'total_chunks': 0,
        'error_details': {}
    }
    
    # Update RAG manager chunk settings with validation
    try:
        st.session_state.rag_manager.text_splitter.chunk_size = max(200, min(chunk_size, 2000))
        st.session_state.rag_manager.text_splitter.chunk_overlap = max(0, min(chunk_overlap, chunk_size // 2))
    except Exception as e:
        st.error(f"❌ **Configuration Error:** Unable to set chunk parameters: {str(e)}")
        return
    
    # Create processing containers with enhanced UI
    progress_container = st.sidebar.container()
    status_container = st.sidebar.container()
    error_container = st.container()
    
    with progress_container:
        st.markdown("### 📄 Processing Documents")
        progress_bar = st.progress(0)
        progress_text = st.empty()
    
    with status_container:
        status_text = st.empty()
        details_text = st.empty()
    
    total_files = len(uploaded_files)
    processed_count = 0
    total_chunks_processed = 0
    failed_files = []
    error_details = {}
    
    try:
        for i, uploaded_file in enumerate(uploaded_files):
            # Update progress indicators
            current_progress = (i + 1) / total_files
            progress_bar.progress(current_progress)
            progress_text.text(f"Processing {i+1}/{total_files}: {uploaded_file.name}")
            status_text.info(f"📄 **Current:** {uploaded_file.name}")
            
            # Update session state
            st.session_state.processing_status.update({
                'progress': current_progress,
                'current_file': uploaded_file.name
            })
            
            # Comprehensive file validation
            try:
                validation_result = validate_uploaded_file_comprehensive(uploaded_file)
                if not validation_result['valid']:
                    error_info = handle_document_processing_error(
                        Exception(validation_result['error']), 
                        uploaded_file.name
                    )
                    failed_files.append(uploaded_file.name)
                    error_details[uploaded_file.name] = error_info
                    details_text.error(f"❌ **Validation Failed:** {uploaded_file.name}")
                    continue
            except Exception as validation_error:
                error_info = handle_document_processing_error(validation_error, uploaded_file.name)
                failed_files.append(uploaded_file.name)
                error_details[uploaded_file.name] = error_info
                details_text.error(f"❌ **Validation Error:** {uploaded_file.name}")
                continue
            
            # Process file with comprehensive error handling
            try:
                details_text.info(f"🔄 **Extracting text from:** {uploaded_file.name}")
                
                # Process the file with progress callback
                def progress_callback(message):
                    details_text.info(f"🔄 {message}")
                
                success, chunk_count = process_file_with_comprehensive_feedback(
                    uploaded_file, progress_callback
                )
                
                if success and chunk_count > 0:
                    processed_count += 1
                    total_chunks_processed += chunk_count
                    details_text.success(f"✅ **Success:** {uploaded_file.name} → {chunk_count} chunks")
                    
                    # Brief success animation
                    time.sleep(0.5)
                else:
                    error_info = handle_document_processing_error(
                        Exception("Processing returned no chunks"), 
                        uploaded_file.name
                    )
                    failed_files.append(uploaded_file.name)
                    error_details[uploaded_file.name] = error_info
                    details_text.error(f"❌ **Processing Failed:** {uploaded_file.name}")
                
            except Exception as processing_error:
                error_info = handle_document_processing_error(processing_error, uploaded_file.name)
                failed_files.append(uploaded_file.name)
                error_details[uploaded_file.name] = error_info
                details_text.error(f"❌ **Error:** {uploaded_file.name} - {str(processing_error)}")
            
            # Small delay for UI responsiveness and user feedback
            time.sleep(0.2)
        
        # Final progress update
        progress_bar.progress(1.0)
        progress_text.text("✅ Processing complete!")
        
        # Display comprehensive results
        with status_container:
            if processed_count > 0:
                st.success(f"""
                ✅ **Processing Complete**
                
                **Successfully processed:** {processed_count}/{total_files} files
                **Total chunks created:** {total_chunks_processed}
                **Documents ready for search:** Yes
                """)
                
                # Update document stats cache
                try:
                    if hasattr(st.session_state.rag_manager.get_document_stats, 'cache_clear'):
                        st.session_state.rag_manager.get_document_stats.cache_clear()
                except:
                    pass
            
            if failed_files:
                st.warning(f"""
                ⚠️ **Some Files Failed**
                
                **Failed files:** {len(failed_files)}/{total_files}
                **Files with errors:** {', '.join(failed_files)}
                
                See error details below for troubleshooting.
                """)
        
        # Display detailed error information for failed files
        if error_details:
            with error_container:
                st.markdown("### 🚨 Processing Errors")
                
                for filename, error_info in error_details.items():
                    with st.expander(f"❌ Error Details: {filename}", expanded=True):
                        display_document_error_summary(error_info, filename)
        
        # Update processing status
        st.session_state.processing_status.update({
            'active': False,
            'completed_time': time.time(),
            'processed_files': processed_count,
            'failed_files': failed_files,
            'total_chunks': total_chunks_processed,
            'error_details': error_details
        })
        
        # Show enhanced processing summary
        show_enhanced_processing_summary(processed_count, total_files, total_chunks_processed, failed_files, error_details)
        
    except Exception as system_error:
        # Handle system-level processing errors
        st.error(f"""
        🚨 **System Processing Error**
        
        A critical error occurred during document processing: {str(system_error)}
        
        **Impact:** Document processing has been halted.
        **Action Required:** Please refresh the page and try again.
        """)
        
        st.session_state.processing_status.update({
            'active': False,
            'system_error': str(system_error)
        })
        
        # Provide recovery options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh Page", key="refresh_after_system_error"):
                st.rerun()
        with col2:
            if st.button("📄 Clear Files", key="clear_files_after_error"):
                if 'document_uploader' in st.session_state:
                    del st.session_state.document_uploader
                st.rerun()
    
    finally:
        # Clean up UI elements after appropriate delay
        time.sleep(2)
        if processed_count > 0 or failed_files:
            # Keep results visible longer if there were actual results
            time.sleep(3)
        
        # Gradual cleanup
        progress_container.empty()
        if not error_details:  # Only clear status if no errors to show
            status_container.empty()

def validate_uploaded_file(uploaded_file) -> bool:
    """Basic validation for backward compatibility"""
    try:
        result = validate_uploaded_file_comprehensive(uploaded_file)
        return result['valid']
    except Exception as e:
        st.sidebar.error(f"File validation error: {str(e)}")
        return False

def validate_uploaded_file_comprehensive(uploaded_file) -> dict:
    """Comprehensive file validation with detailed error reporting"""
    try:
        # Check if file exists and has content
        if not uploaded_file:
            return {
                'valid': False,
                'error': 'No file provided',
                'error_type': 'missing_file'
            }
        
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return {
                'valid': False,
                'error': f'File size ({uploaded_file.size / (1024*1024):.1f}MB) exceeds maximum limit (10MB)',
                'error_type': 'size_limit'
            }
        
        # Check for empty files
        if uploaded_file.size == 0:
            return {
                'valid': False,
                'error': 'File is empty (0 bytes)',
                'error_type': 'empty_file'
            }
        
        # Check file extension
        allowed_extensions = ['pdf', 'txt', 'md', 'docx', 'html', 'htm']
        file_parts = uploaded_file.name.lower().split('.')
        
        if len(file_parts) < 2:
            return {
                'valid': False,
                'error': 'File has no extension',
                'error_type': 'no_extension'
            }
        
        file_extension = file_parts[-1]
        if file_extension not in allowed_extensions:
            return {
                'valid': False,
                'error': f'Unsupported file type: .{file_extension}. Supported: {", ".join(allowed_extensions)}',
                'error_type': 'unsupported_format'
            }
        
        # Check filename for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in uploaded_file.name for char in invalid_chars):
            return {
                'valid': False,
                'error': 'Filename contains invalid characters',
                'error_type': 'invalid_filename'
            }
        
        # Basic content validation (try to read first few bytes)
        try:
            content_sample = uploaded_file.read(100)
            uploaded_file.seek(0)  # Reset file pointer
            
            # Check if file appears to be binary when it should be text
            if file_extension in ['txt', 'md', 'html', 'htm']:
                try:
                    content_sample.decode('utf-8')
                except UnicodeDecodeError:
                    return {
                        'valid': False,
                        'error': 'Text file contains invalid characters or is corrupted',
                        'error_type': 'encoding_error'
                    }
        except Exception as read_error:
            return {
                'valid': False,
                'error': f'Unable to read file: {str(read_error)}',
                'error_type': 'read_error'
            }
        
        return {
            'valid': True,
            'error': None,
            'error_type': None,
            'file_info': {
                'name': uploaded_file.name,
                'size': uploaded_file.size,
                'extension': file_extension
            }
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Validation failed: {str(e)}',
            'error_type': 'validation_error'
        }

def process_file_with_feedback(uploaded_file) -> tuple[bool, int]:
    """Process file and return success status and chunk count (backward compatibility)"""
    try:
        return process_file_with_comprehensive_feedback(uploaded_file, None)
    except Exception as e:
        st.sidebar.error(f"Processing error: {str(e)}")
        return False, 0

def process_file_with_comprehensive_feedback(uploaded_file, progress_callback=None) -> tuple[bool, int]:
    """Process file with comprehensive feedback and error handling"""
    try:
        if progress_callback:
            progress_callback("Initializing file processing...")
        
        # Validate RAG manager availability
        if not hasattr(st.session_state, 'rag_manager') or not st.session_state.rag_manager:
            raise Exception("RAG manager not available")
        
        if progress_callback:
            progress_callback("Validating file format...")
        
        # Additional format-specific validation
        file_extension = uploaded_file.name.lower().split('.')[-1]
        
        # Check file content based on extension
        if file_extension == 'pdf':
            if progress_callback:
                progress_callback("Validating PDF structure...")
            # Basic PDF validation - check for PDF header
            content_start = uploaded_file.read(10)
            uploaded_file.seek(0)
            if not content_start.startswith(b'%PDF-'):
                raise Exception("Invalid PDF file format")
        
        elif file_extension == 'docx':
            if progress_callback:
                progress_callback("Validating DOCX structure...")
            # Basic DOCX validation - check for ZIP signature (DOCX is a ZIP file)
            content_start = uploaded_file.read(4)
            uploaded_file.seek(0)
            if not content_start.startswith(b'PK'):
                raise Exception("Invalid DOCX file format")
        
        if progress_callback:
            progress_callback("Processing document with RAG manager...")
        
        # Process the file using RAG manager with enhanced error handling
        try:
            success, chunk_count = st.session_state.rag_manager.process_uploaded_file(
                uploaded_file, 
                progress_callback
            )
            
            if not success:
                raise Exception("RAG manager returned failure status")
            
            if chunk_count == 0:
                raise Exception("No text chunks were extracted from the document")
            
            if progress_callback:
                progress_callback(f"Successfully created {chunk_count} text chunks")
            
            return True, chunk_count
            
        except Exception as rag_error:
            # Handle specific RAG processing errors
            error_str = str(rag_error).lower()
            
            if "embedding" in error_str:
                raise Exception("Failed to generate embeddings for document chunks")
            elif "database" in error_str:
                raise Exception("Failed to store document chunks in database")
            elif "extraction" in error_str:
                raise Exception("Failed to extract text from document")
            else:
                raise Exception(f"Document processing failed: {str(rag_error)}")
    
    except Exception as e:
        # Log the error for debugging
        error_message = str(e)
        
        if progress_callback:
            progress_callback(f"Error: {error_message}")
        
        # Provide specific error context
        if "not available" in error_message:
            raise Exception("Document processing system is not properly initialized")
        elif "Invalid" in error_message and "format" in error_message:
            raise Exception(f"File format validation failed: {error_message}")
        elif "embedding" in error_message:
            raise Exception("Failed to generate document embeddings - check AI service configuration")
        elif "database" in error_message:
            raise Exception("Failed to store document in database - check database connection")
        else:
            raise Exception(f"Document processing error: {error_message}")
    
    return False, 0

def show_processing_summary(processed_count: int, total_files: int, total_chunks: int, failed_files: List[str]):
    """Show basic processing summary (backward compatibility)"""
    show_enhanced_processing_summary(processed_count, total_files, total_chunks, failed_files, {})

def show_enhanced_processing_summary(processed_count: int, total_files: int, total_chunks: int, failed_files: List[str], error_details: dict):
    """Show comprehensive processing summary with error analysis"""
    with st.sidebar.expander("📊 Processing Summary", expanded=True):
        # Overall statistics
        success_rate = (processed_count/total_files)*100 if total_files > 0 else 0
        
        st.markdown(f"""
        ### 📈 **Processing Results**
        
        **Files Processed:** {processed_count}/{total_files}  
        **Success Rate:** {success_rate:.1f}%  
        **Total Chunks Created:** {total_chunks}  
        **Average Chunks per File:** {total_chunks/processed_count if processed_count > 0 else 0:.1f}
        """)
        
        # Success indicator
        if success_rate == 100:
            st.success("🎉 All files processed successfully!")
        elif success_rate >= 75:
            st.success("✅ Most files processed successfully")
        elif success_rate >= 50:
            st.warning("⚠️ Some files had issues")
        elif success_rate > 0:
            st.warning("⚠️ Many files failed to process")
        else:
            st.error("❌ No files were processed successfully")
        
        # Failed files analysis
        if failed_files:
            st.markdown("### ❌ **Failed Files Analysis**")
            
            # Categorize errors
            error_categories = {}
            for filename in failed_files:
                if filename in error_details:
                    error_type = error_details[filename].get('type', 'unknown_error')
                    if error_type not in error_categories:
                        error_categories[error_type] = []
                    error_categories[error_type].append(filename)
                else:
                    if 'unknown_error' not in error_categories:
                        error_categories['unknown_error'] = []
                    error_categories['unknown_error'].append(filename)
            
            # Display categorized errors
            for error_type, files in error_categories.items():
                error_icon = {
                    'size_error': '📏',
                    'format_error': '📄',
                    'corruption_error': '💥',
                    'permission_error': '🔒',
                    'network_error': '🌐',
                    'unknown_error': '❓'
                }.get(error_type, '❓')
                
                error_name = {
                    'size_error': 'File Size Issues',
                    'format_error': 'Format Issues',
                    'corruption_error': 'Corrupted Files',
                    'permission_error': 'Access Issues',
                    'network_error': 'Network Issues',
                    'unknown_error': 'Unknown Errors'
                }.get(error_type, 'Unknown Errors')
                
                st.markdown(f"**{error_icon} {error_name}:** {len(files)} file(s)")
                for file in files:
                    st.markdown(f"  • {file}")
        
        # Next steps and recommendations
        if processed_count > 0:
            st.markdown("### 🚀 **Next Steps**")
            st.markdown("""
            ✅ **Documents Ready for Use:**
            - Ask questions about your uploaded documents
            - The AI will automatically search relevant content
            - Look for document context indicators in responses
            """)
            
            if total_chunks > 100:
                st.info("💡 **Tip:** With many document chunks, try specific questions for better results.")
            
        if failed_files:
            st.markdown("### 💡 **Troubleshooting Tips**")
            
            # Provide specific tips based on error types
            if any('size_error' in error_details.get(f, {}).get('type', '') for f in failed_files):
                st.markdown("📏 **For large files:** Try splitting documents or reducing file size")
            
            if any('format_error' in error_details.get(f, {}).get('type', '') for f in failed_files):
                st.markdown("📄 **For format issues:** Convert to PDF, DOCX, or TXT format")
            
            if any('corruption_error' in error_details.get(f, {}).get('type', '') for f in failed_files):
                st.markdown("💥 **For corrupted files:** Re-save or re-download the documents")
            
            st.markdown("🔄 **General:** You can retry failed files or continue with successfully processed documents")
        
        # Performance metrics
        if processed_count > 0:
            processing_time = st.session_state.processing_status.get('completed_time', time.time()) - st.session_state.processing_status.get('start_time', time.time())
            if processing_time > 0:
                st.markdown(f"""
                ### ⚡ **Performance**
                **Processing Time:** {processing_time:.1f} seconds  
                **Files per Second:** {processed_count/processing_time:.1f}  
                **Chunks per Second:** {total_chunks/processing_time:.1f}
                """)
        
        # Storage information
        if total_chunks > 0:
            estimated_storage = total_chunks * 0.5  # Rough estimate in KB
            st.markdown(f"""
            ### 💾 **Storage Impact**
            **Estimated Storage Used:** {estimated_storage:.1f} KB  
            **Document Chunks in Database:** {total_chunks}  
            **Search Index Updated:** Yes
            """)
        
        # Action buttons
        st.markdown("### 🎯 **Actions**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Test Document Search", key="test_doc_search"):
                st.session_state.show_search_test = True
                st.rerun()
        
        with col2:
            if st.button("📊 View Document Stats", key="view_doc_stats"):
                st.session_state.show_doc_stats = True
                st.rerun()
        
        # Clear processing status button
        if st.button("🗑️ Clear Processing History", key="clear_processing_history"):
            if 'processing_status' in st.session_state:
                del st.session_state.processing_status
            st.rerun()

def clear_all_documents() -> bool:
    """Clear all stored documents from the database"""
    try:
        return st.session_state.rag_manager.clear_all_documents()
    except Exception as e:
        st.sidebar.error(f"Error clearing documents: {str(e)}")
        return False

def render_chat_controls():
    """Render simplified chat controls in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💬 Chat Controls")
    
    # Only show clear chat button
    if st.sidebar.button("🗑️ Clear Chat", help="Clear all messages", use_container_width=True):
        st.session_state.messages = []
        st.sidebar.success("Chat cleared!")
        st.rerun()

def render_chat_history():
    """Render chat message history"""
    for message in st.session_state.messages:
        render_message(message)

def render_message(message: Dict[str, Any]):
    """Render a single chat message with enhanced metadata and error handling"""
    role = message["role"]
    content = message["content"]
    timestamp = message.get("timestamp", 0)
    time_str = time.strftime("%H:%M", time.localtime(timestamp)) if timestamp else ""
    
    # Handle system messages (like model switches)
    if role == "system":
        is_error = message.get("error", False)
        message_class = "system-message"
        if is_error:
            message_class += " error-message"
        
        st.markdown(f"""
        <div class="chat-message {message_class}">
            <div style="text-align: center; font-style: italic;">
                <small style="color: #d1d5db;">{time_str}</small><br>
                <strong>🔔 System:</strong> {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if role == "user":
        # Escape HTML in user content for security
        safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        st.markdown(f"""
        <div class="chat-message user-message">
            <div style="margin-bottom: 0.5rem;">
                <strong>👤 You</strong> 
                <small style="color: #9ca3af; float: right;">{time_str}</small>
            </div>
            <div style="clear: both;">{safe_content}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Assistant messages with enhanced error handling and status indicators
        model_used = message.get("model", "unknown")
        context_used = message.get("context_used", False)
        context_chunks = message.get("context_chunks", 0)
        is_error = message.get("error", False)
        
        # Always show PharmGPT branding
        model_icon = "💊"
        model_display = "PharmGPT"
        
        # Build status indicators with enhanced information
        status_indicators = []
        
        if is_error:
            status_indicators.append("❌ Error")
        elif context_used and context_chunks > 0:
            status_indicators.append(f"📚 {context_chunks} docs")
        elif context_chunks == 0 and not is_error:
            status_indicators.append("🧠 General knowledge")
        
        # Add model availability indicator
        if hasattr(st.session_state, 'model_manager'):
            if not st.session_state.model_manager.is_model_available():
                status_indicators.append("⚠️ Model unavailable")
        
        status_text = " • ".join(status_indicators)
        if status_text:
            status_text = f" • {status_text}"
        
        # Determine message styling
        message_class = "assistant-message"
        if is_error:
            message_class = "error-message"
        
        # Format content with basic markdown support
        formatted_content = format_message_content(content)
        
        # Add error-specific styling and recovery options
        error_recovery_html = ""
        if is_error:
            error_recovery_html = """
            <div style="margin-top: 0.75rem; padding: 0.5rem; background-color: rgba(239, 68, 68, 0.1); border-radius: 0.5rem; border-left: 3px solid var(--error-color);">
                <small style="color: var(--error-color); font-weight: 600;">💡 Try:</small>
                <small style="color: var(--text-color); display: block; margin-top: 0.25rem;">
                • Refresh the page and try again<br>
                • Switch to a different model<br>
                • Simplify your question
                </small>
            </div>
            """
        
        st.markdown(f"""
        <div class="chat-message {message_class}">
            <div style="margin-bottom: 0.5rem;">
                <strong>{model_icon} {model_display}</strong>
                <small style="color: #9ca3af; float: right;">{time_str}{status_text}</small>
            </div>
            <div style="clear: both; line-height: 1.6;">
                {formatted_content}
            </div>
            {error_recovery_html}
        </div>
        """, unsafe_allow_html=True)

def format_message_content(content: str) -> str:
    """Format message content with enhanced markdown support and safety"""
    # Escape HTML for security
    safe_content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Convert markdown-like formatting
    import re
    
    # Bold text
    safe_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', safe_content)
    
    # Italic text
    safe_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', safe_content)
    
    # Inline code
    safe_content = re.sub(r'`(.*?)`', r'<code style="background-color: var(--secondary-bg); padding: 0.2rem 0.4rem; border-radius: 0.3rem; font-family: monospace;">\1</code>', safe_content)
    
    # Code blocks
    safe_content = re.sub(
        r'```(.*?)```', 
        r'<pre style="background-color: var(--secondary-bg); padding: 1rem; border-radius: 0.5rem; overflow-x: auto; margin: 0.5rem 0;"><code>\1</code></pre>', 
        safe_content, 
        flags=re.DOTALL
    )
    
    # Convert line breaks to HTML
    safe_content = safe_content.replace('\n', '<br>')
    
    # Convert URLs to links (basic implementation)
    url_pattern = r'(https?://[^\s<>"]+)'
    safe_content = re.sub(
        url_pattern, 
        r'<a href="\1" target="_blank" style="color: var(--primary-color); text-decoration: underline;">\1</a>', 
        safe_content
    )
    
    return safe_content

def render_processing_status_indicator():
    """Render document processing status indicator"""
    if 'processing_status' in st.session_state and st.session_state.processing_status.get('active', False):
        status = st.session_state.processing_status
        progress = status.get('progress', 0)
        current_file = status.get('current_file', '')
        
        st.markdown("**Processing Documents**")
        st.progress(progress)
        if current_file:
            st.caption(f"📄 {current_file}")
    else:
        # Show document availability status
        stats = st.session_state.rag_manager.get_document_stats()
        if stats['total_chunks'] > 0:
            st.markdown("**📚 RAG Active**")
            st.caption(f"{stats['total_chunks']} chunks ready")
        else:
            st.markdown("**📚 No Documents**")
            st.caption("Upload docs for enhanced responses")

# Removed test_responsive_design function - no longer needed

def render_message_input():
    """Render enhanced message input interface with comprehensive status and error handling"""
    st.markdown("---")
    
    # Enhanced status display with error handling
    try:
        # Model status section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            model_available = st.session_state.model_manager.is_model_available()
            model_info = st.session_state.model_manager.get_model_info()
            
            if model_info:
                status_icon = "🟢" if model_available else "🔴"
                status_text = "Available" if model_available else "Unavailable"
                
                st.markdown(f"""
                <div class="status-indicator status-{'online' if model_available else 'offline'}">
                    <span class="status-dot"></span>
                    <strong>PharmGPT:</strong> {status_text}
                </div>
                """, unsafe_allow_html=True)
                
                if not model_available:
                    st.error("⚠️ Mistral API key required. Check your configuration.")
            else:
                st.error("❌ No model information available")
        
        with col2:
            # Document context status with error handling
            try:
                stats = st.session_state.rag_manager.get_document_stats()
                chunk_count = stats.get('total_chunks', 0)
                
                if chunk_count > 0:
                    st.markdown(f"""
                    <div class="status-indicator status-online">
                        <span class="status-dot"></span>
                        <strong>Documents:</strong> {chunk_count} chunks ready
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="status-indicator status-offline">
                        <span class="status-dot"></span>
                        <strong>Documents:</strong> No context available
                    </div>
                    """, unsafe_allow_html=True)
            except Exception as rag_error:
                st.warning(f"⚠️ Document system error: {str(rag_error)}")
        
        # Enhanced chat input with dynamic placeholder and validation
        model_available = st.session_state.model_manager.is_model_available()
        stats = st.session_state.rag_manager.get_document_stats()
        chunk_count = stats.get('total_chunks', 0)
        
        # Dynamic placeholder based on system status
        if not model_available:
            placeholder_text = "Mistral API key required - check configuration"
        elif chunk_count > 0:
            placeholder_text = f"Ask me about pharmacology... (I can search {chunk_count} document chunks)"
        else:
            placeholder_text = "Ask me about pharmacology... (using general knowledge)"
        
        # Input validation and enhancement
        user_input = st.chat_input(
            placeholder=placeholder_text,
            disabled=not model_available,
            key="chat_input"
        )
        
        # Additional input validation
        if user_input and model_available:
            # Only check for maximum length, allow any minimum length including "hi"
            if len(user_input) > 2000:
                st.warning("⚠️ Question is too long. Please keep it under 2000 characters.")
                return None
            
            # Check for potentially problematic content
            if user_input.strip().lower() in ['test', 'hello', 'hi']:
                st.info("💡 Tip: Try asking specific pharmacology questions for better responses!")
        
        return user_input if model_available else None
        
    except Exception as input_error:
        st.error(f"""
        🚨 **Input System Error**
        
        The message input system encountered an error: {str(input_error)}
        
        **Recovery Actions:**
        - Refresh the page
        - Check your internet connection
        - Contact support if the issue persists
        """)
        
        if st.button("🔄 Refresh Input System", key="refresh_input_system"):
            st.rerun()
        
        return None

def render_enhanced_ui_controls():
    """Render minimal UI controls"""
    # Removed all test buttons, performance monitoring, and error reporting
    # Keep only essential functionality
    pass

# ----------------------------
# Conversation Management
# ----------------------------
def export_conversation():
    """Export conversation history as downloadable file"""
    if not st.session_state.messages:
        st.sidebar.warning("No messages to export")
        return
    
    # Create export content
    export_lines = []
    export_lines.append("# Simple Chatbot Conversation Export")
    export_lines.append(f"Exported on: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    export_lines.append(f"Total messages: {len(st.session_state.messages)}")
    export_lines.append("")
    
    for i, message in enumerate(st.session_state.messages, 1):
        role = message["role"]
        content = message["content"]
        timestamp = message.get("timestamp", 0)
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp)) if timestamp else "Unknown"
        
        if role == "user":
            export_lines.append(f"## Message {i} - User ({time_str})")
            export_lines.append(content)
        elif role == "assistant":
            model = message.get("model", "unknown")
            context_used = message.get("context_used", False)
            context_chunks = message.get("context_chunks", 0)
            
            export_lines.append(f"## Message {i} - Assistant ({time_str})")
            export_lines.append(f"**Model:** {model}")
            if context_used:
                export_lines.append(f"**Context:** {context_chunks} document chunks used")
            export_lines.append("")
            export_lines.append(content)
        elif role == "system":
            export_lines.append(f"## System Message ({time_str})")
            export_lines.append(content)
        
        export_lines.append("")
        export_lines.append("---")
        export_lines.append("")
    
    export_content = "\n".join(export_lines)
    
    # Create download button
    st.sidebar.download_button(
        label="📄 Download as Markdown",
        data=export_content,
        file_name=f"chatbot_conversation_{time.strftime('%Y%m%d_%H%M%S')}.md",
        mime="text/markdown"
    )

# ----------------------------
# Message Processing
# ----------------------------
def handle_api_error(error: Exception, model_type: str) -> str:
    """Handle API errors with user-friendly messages and fallback suggestions"""
    error_str = str(error).lower()
    
    if "api key" in error_str or "authentication" in error_str:
        return f"""
        🔑 **API Authentication Error**
        
        The {model_type} model API key is missing or invalid.
        
        **To fix this:**
        1. Check your Streamlit secrets configuration
        2. Ensure GROQ_API_KEY is properly set
        3. Verify the API key is valid and active
        
        **Current Status:** {model_type.title()} model unavailable
        """
    elif "rate limit" in error_str or "quota" in error_str:
        return f"""
        ⏱️ **Rate Limit Exceeded**
        
        You've reached the rate limit for the {model_type} model.
        
        **What you can do:**
        - Wait a few minutes before trying again
        - Switch to the other model if available
        - Check your API usage limits
        
        **Tip:** Premium models typically have higher rate limits.
        """
    elif "network" in error_str or "connection" in error_str:
        return f"""
        🌐 **Network Connection Error**
        
        Unable to connect to the {model_type} model API.
        
        **Troubleshooting:**
        - Check your internet connection
        - Try refreshing the page
        - The API service might be temporarily unavailable
        
        **Status:** Retrying automatically...
        """
    elif "timeout" in error_str:
        return f"""
        ⏰ **Request Timeout**
        
        The {model_type} model took too long to respond.
        
        **Solutions:**
        - Try a shorter question
        - Switch to the fast model for quicker responses
        - Retry your request
        
        **Note:** Complex questions may take longer to process.
        """
    else:
        return f"""
        ❌ **Unexpected Error**
        
        An unexpected error occurred with the {model_type} model: {str(error)}
        
        **What to try:**
        - Refresh the page and try again
        - Switch to the other model
        - Simplify your question
        
        **If the problem persists:** Check the application logs for more details.
        """

def handle_rag_error(error: Exception) -> str:
    """Handle RAG system errors with helpful guidance"""
    error_str = str(error).lower()
    
    if "database" in error_str or "connection" in error_str:
        return """
        🗄️ **Database Connection Error**
        
        Unable to search your uploaded documents.
        
        **Impact:** Using general knowledge instead of your documents.
        **Action:** Your question will still be answered using the AI's built-in knowledge.
        """
    elif "embedding" in error_str:
        return """
        🧠 **Document Processing Error**
        
        Unable to process document embeddings for search.
        
        **Impact:** Document search temporarily unavailable.
        **Fallback:** Answering with general pharmacology knowledge.
        """
    elif "search" in error_str or "retrieval" in error_str:
        return """
        🔍 **Document Search Error**
        
        Unable to search through your uploaded documents.
        
        **Impact:** No document context will be used for this response.
        **Note:** The AI will still provide helpful answers using general knowledge.
        """
    else:
        return f"""
        📚 **Document System Error**
        
        Document assistance temporarily unavailable: {str(error)}
        
        **Fallback:** Using general AI knowledge to answer your question.
        **Tip:** You can continue asking questions normally.
        """

def display_error_with_recovery(error_message: str, error_type: str = "error", recovery_actions: list = None):
    """Display error message with recovery actions"""
    if error_type == "critical":
        st.error(error_message)
    elif error_type == "warning":
        st.warning(error_message)
    else:
        st.info(error_message)
    
    if recovery_actions:
        st.markdown("**Available Actions:**")
        cols = st.columns(len(recovery_actions))
        
        for i, action in enumerate(recovery_actions):
            with cols[i]:
                if st.button(action['label'], key=f"recovery_action_{i}_{time.time()}"):
                    if action.get('callback'):
                        action['callback']()
                    if action.get('rerun', True):
                        st.rerun()



def process_user_message(user_input: str):
    """Process user message and generate AI response with RAG integration"""
    if not user_input.strip():
        return
    
    # Add user message to history
    user_message = {
        "role": "user",
        "content": user_input,
        "timestamp": time.time()
    }
    st.session_state.messages.append(user_message)
    
    # Check model availability
    if not st.session_state.model_manager.is_model_available():
        error_message = """
        🚫 **Mistral API Unavailable**
        
        The Mistral AI model is currently unavailable.
        
        **Please:**
        - Check your MISTRAL_API_KEY configuration
        - Verify your API key is valid
        - Check your internet connection
        """
        
        st.error(error_message)
        
        # Add error message to chat history
        assistant_message = {
            "role": "assistant",
            "content": "I'm currently unable to process your request due to API configuration issues. Please check your Mistral API key.",
            "timestamp": time.time(),
            "model": "mistral",
            "error": True,
            "context_used": False,
            "context_chunks": 0
        }
        st.session_state.messages.append(assistant_message)
        st.rerun()
        return
    
    # Generate AI response with RAG integration
    try:
        with st.spinner("🤖 Generating response with Mistral AI..."):
            # Get RAG context if available
            context = ""
            context_chunks = 0
            
            try:
                # Check if documents are available
                stats = st.session_state.rag_manager.get_document_stats()
                if stats['total_chunks'] > 0:
                    with st.spinner("🔍 Searching document context..."):
                        context = st.session_state.rag_manager.search_relevant_context(user_input, max_chunks=5)
                        if context and context.strip():
                            # Count actual content chunks
                            context_chunks = len([chunk for chunk in context.split('\n\n') if chunk.strip()])
                            if context_chunks > 0:
                                st.success(f"📚 Found {context_chunks} relevant document chunks")
                            else:
                                st.info("📚 No relevant document context found")
                                context = ""
                        else:
                            st.info("📚 No relevant document context found")
                            context = ""
                else:
                    st.info("📚 No documents available - using general knowledge")
            except Exception as rag_error:
                st.warning(f"⚠️ Document search error: {str(rag_error)}")
                st.info("📚 Falling back to general knowledge")
                context = ""
                context_chunks = 0
            
            # Generate AI response with context
            try:
                with st.spinner("✨ Generating detailed response..."):
                    ai_response = st.session_state.model_manager.generate_response(
                        message=user_input,
                        context=context if context else None
                    )
                    
                    if ai_response and not ai_response.startswith("Error:") and not ai_response.startswith("Mistral API error:"):
                        # Success - add to message history
                        assistant_message = {
                            "role": "assistant",
                            "content": ai_response,
                            "timestamp": time.time(),
                            "model": "mistral",
                            "context_used": bool(context),
                            "context_chunks": context_chunks,
                            "error": False
                        }
                        st.session_state.messages.append(assistant_message)
                        
                        # Show success indicators
                        if context_chunks > 0:
                            st.success(f"✅ Response generated using {context_chunks} document sources")
                        else:
                            st.success("✅ Response generated using general pharmacology knowledge")
                    else:
                        raise Exception(ai_response or "Empty response from model")
                        
            except Exception as model_error:
                # Handle API errors
                error_str = str(model_error)
                
                if "api key" in error_str.lower() or "authentication" in error_str.lower():
                    error_message = """
                    🔑 **API Authentication Error**
                    
                    Your Mistral API key is invalid or missing.
                    
                    **To fix:**
                    - Check your MISTRAL_API_KEY in environment variables
                    - Verify the API key is correct and active
                    - Try refreshing the page
                    """
                elif "rate limit" in error_str.lower() or "quota" in error_str.lower():
                    error_message = """
                    ⏱️ **Rate Limit Exceeded**
                    
                    You've reached your Mistral API rate limit.
                    
                    **What to do:**
                    - Wait a few minutes before trying again
                    - Check your API usage limits
                    - Consider upgrading your plan
                    """
                elif "timeout" in error_str.lower():
                    error_message = """
                    ⏰ **Request Timeout**
                    
                    The request took too long to process.
                    
                    **Try:**
                    - Asking a shorter question
                    - Retrying your request
                    - Checking your internet connection
                    """
                else:
                    error_message = f"""
                    ❌ **API Error**
                    
                    Mistral API error: {error_str}
                    
                    **Try:**
                    - Refreshing the page
                    - Checking your API configuration
                    - Retrying your request
                    """
                
                st.error(error_message)
                
                # Add error response to chat history
                error_response = "I apologize, but I'm currently experiencing technical difficulties. Please check the error message above and try again."
                
                assistant_message = {
                    "role": "assistant",
                    "content": error_response,
                    "timestamp": time.time(),
                    "model": "mistral",
                    "error": True,
                    "context_used": False,
                    "context_chunks": 0
                }
                st.session_state.messages.append(assistant_message)
    
    except Exception as unexpected_error:
        # Handle unexpected errors
        st.error(f"""
        🚨 **Unexpected Error**
        
        An unexpected error occurred: {str(unexpected_error)}
        
        **Please:**
        - Refresh the page and try again
        - Check your internet connection
        - Contact support if the issue persists
        """)
        
        # Add system error message to chat history
        system_error_message = {
            "role": "system",
            "content": f"System error: {str(unexpected_error)}",
            "timestamp": time.time(),
            "error": True
        }
        st.session_state.messages.append(system_error_message)
    
    # Always rerun to update the UI
    st.rerun()

# ----------------------------
# Main Application
# ----------------------------
def main():
    """Main application function with comprehensive error handling and enhanced UI"""
    try:
        # Initialize session state with error handling
        try:
            initialize_session_state()
        except Exception as init_error:
            st.error(f"""
            🚨 **Initialization Error**
            
            Failed to initialize the application: {str(init_error)}
            
            **Recovery Actions:**
            - Refresh the page
            - Clear browser cache
            - Check internet connection
            """)
            
            if st.button("🔄 Retry Initialization", key="retry_init"):
                st.rerun()
            return
        
        # Apply enhanced dark mode styling with error handling
        try:
            apply_dark_mode_styling()
        except Exception as style_error:
            st.warning(f"⚠️ Styling error: {str(style_error)}")
            # Continue without custom styling
        
        # Check database schema setup with enhanced error handling
        try:
            if not st.session_state.db_manager.check_schema_exists():
                st.title("💬 Simple Chatbot - Database Setup Required")
                st.markdown("---")
                
                st.warning("⚠️ Database schema not found. Please set up the database first.")
                
                # Enhanced setup instructions with error handling
                try:
                    if st.session_state.db_manager.setup_database_schema():
                        st.rerun()
                except Exception as schema_error:
                    st.error(f"""
                    🗄️ **Database Setup Error**
                    
                    Failed to set up database schema: {str(schema_error)}
                    
                    **Manual Setup Required:**
                    1. Go to your Supabase Dashboard
                    2. Navigate to SQL Editor
                    3. Run the schema from simple_chatbot_schema.sql
                    4. Refresh this application
                    """)
                    
                    if st.button("🔄 Retry Schema Check", key="retry_schema"):
                        st.rerun()
                
                return
        except Exception as db_error:
            st.error(f"""
            🗄️ **Database Connection Error**
            
            Unable to connect to the database: {str(db_error)}
            
            **Troubleshooting:**
            - Check your Supabase credentials
            - Verify internet connection
            - Ensure database is accessible
            """)
            
            if st.button("🔄 Retry Database Connection", key="retry_db"):
                st.rerun()
            return
        
        # Render header with error handling
        try:
            render_header()
        except Exception as header_error:
            st.error(f"Header rendering error: {str(header_error)}")
        
        # Sidebar components with comprehensive error handling
        try:
            with st.sidebar:
                # Minimal model check - only show if there's an issue
                try:
                    if not st.session_state.model_manager.is_model_available():
                        st.sidebar.error("⚠️ Mistral API key required")
                        with st.sidebar.expander("🔑 Setup"):
                            st.markdown("Add `MISTRAL_API_KEY` to Streamlit secrets")
                except Exception:
                    pass  # Silent fail - don't clutter sidebar
                
                # Document upload is now inline above chat input
                # No sidebar document upload needed
                
                # Chat controls with error handling
                try:
                    render_chat_controls()
                except Exception as control_error:
                    st.sidebar.error(f"Chat controls error: {str(control_error)}")
                
                # Enhanced UI controls
                try:
                    render_enhanced_ui_controls()
                except Exception as ui_error:
                    st.sidebar.warning(f"UI controls error: {str(ui_error)}")
        
        except Exception as sidebar_error:
            st.error(f"Sidebar error: {str(sidebar_error)}")
        
        # Main chat area with enhanced layout and error handling
        try:
            # Removed responsive design test
            
            # Enhanced main area layout
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("### 💬 Chat")
            
            with col2:
                # Document processing status indicator with error handling
                try:
                    render_processing_status_indicator()
                except Exception as status_error:
                    st.warning(f"Status indicator error: {str(status_error)}")
            
            # Chat history rendering with error handling
            try:
                render_chat_history()
            except Exception as history_error:
                st.error(f"""
                📜 **Chat History Error**
                
                Unable to display chat history: {str(history_error)}
                
                **What you can do:**
                - Continue chatting (new messages will work)
                - Clear chat history to reset
                - Refresh the page
                """)
                
                if st.button("🗑️ Clear Chat History", key="clear_history_error"):
                    st.session_state.messages = []
                    st.rerun()
            
            # Document upload inline (above chat input)
            try:
                render_document_upload_inline()
            except Exception as doc_error:
                st.error(f"Document upload error: {str(doc_error)}")
            
            # Message input with comprehensive error handling
            try:
                user_input = render_message_input()
                
                # Process user message if provided
                if user_input:
                    try:
                        process_user_message(user_input)
                    except Exception as process_error:
                        st.error(f"""
                        💬 **Message Processing Error**
                        
                        Failed to process your message: {str(process_error)}
                        
                        **Your message:** "{user_input}"
                        
                        **Recovery Options:**
                        - Try rephrasing your question
                        - Check model availability
                        - Refresh the page and try again
                        """)
                        
                        # Add error message to chat history for context
                        error_message = {
                            "role": "system",
                            "content": f"Failed to process message: {str(process_error)}",
                            "timestamp": time.time(),
                            "error": True
                        }
                        st.session_state.messages.append(error_message)
                        st.rerun()
            
            except Exception as input_error:
                st.error(f"""
                ⌨️ **Input System Error**
                
                The message input system is not working: {str(input_error)}
                
                **Troubleshooting:**
                - Refresh the page
                - Check browser compatibility
                - Try a different browser
                """)
                
                if st.button("🔄 Refresh Application", key="refresh_app_input_error"):
                    st.rerun()
        
        except Exception as main_area_error:
            st.error(f"""
            🏠 **Main Area Error**
            
            The main application area encountered an error: {str(main_area_error)}
            
            **System Status:**
            - Application partially functional
            - Some features may be unavailable
            - Data should be preserved
            
            **Recommended Actions:**
            1. Refresh the page
            2. Clear browser cache if issues persist
            3. Contact support with error details
            """)
            
            # Provide emergency recovery options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Full Refresh", key="full_refresh"):
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Clear Session", key="clear_session"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
            
            with col3:
                if st.button("📋 Show Debug Info", key="show_debug"):
                    st.json({
                        'error': str(main_area_error),
                        'session_keys': list(st.session_state.keys()),
                        'timestamp': time.time()
                    })
    
    except Exception as critical_error:
        # Critical application error - last resort error handling
        st.error(f"""
        🚨 **Critical Application Error**
        
        The application has encountered a critical error and cannot continue normally.
        
        **Error Details:** {str(critical_error)}
        
        **Emergency Recovery:**
        """)
        
        # Emergency recovery interface
        st.markdown("### 🆘 Emergency Recovery Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Force Restart", key="force_restart"):
                # Clear all session state and restart
                st.session_state.clear()
                st.rerun()
        
        with col2:
            if st.button("📞 Contact Support", key="contact_support"):
                st.markdown("""
                **Support Information:**
                - Include the error message above
                - Mention what you were doing when the error occurred
                - Provide browser and device information
                """)
        
        # Show minimal debug information
        with st.expander("🔍 Debug Information", expanded=False):
            st.code(f"""
            Error: {str(critical_error)}
            Timestamp: {time.time()}
            Session State Keys: {list(st.session_state.keys()) if hasattr(st, 'session_state') else 'Not available'}
            """)
        
        # Provide basic functionality as fallback
        st.markdown("### 💡 Basic Functionality")
        st.info("You can try using the basic chat functionality below:")
        
        basic_input = st.text_input("Enter your question:", key="emergency_input")
        if st.button("Send", key="emergency_send") and basic_input:
            st.write(f"**You:** {basic_input}")
            st.write("**System:** I apologize, but the application is experiencing technical difficulties. Please try refreshing the page or contact support.")

# ----------------------------
# Application Entry Point
# ----------------------------
if __name__ == "__main__":
    main()