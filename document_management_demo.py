"""
Document Management Demo
Demonstrates the document management functionality for the pharmacology chat app
"""

import streamlit as st
import os
from datetime import datetime
from typing import Optional

# Import document management components
from document_manager import DocumentManager
from document_ui import DocumentInterface

# Import authentication components for user context
from session_manager import SessionManager
from auth_manager import AuthenticationManager

# Configure Streamlit page
st.set_page_config(
    page_title="📚 Document Management Demo",
    page_icon="📚",
    layout="wide"
)

def initialize_demo_session():
    """Initialize demo session with mock user"""
    if 'demo_user_id' not in st.session_state:
        st.session_state.demo_user_id = "demo-user-123"
        st.session_state.demo_user_email = "demo@example.com"

def render_demo_header():
    """Render demo header with user info"""
    st.title("📚 Document Management System Demo")
    st.markdown("**Demo User:** `demo@example.com`")
    st.markdown("---")
    
    st.markdown("""
    This demo showcases the document management functionality for the pharmacology chat application:
    
    **Features:**
    - 📁 **File Upload**: Upload PDF, DOCX, TXT, and HTML files
    - 🌐 **URL Import**: Extract content from web pages
    - 🔍 **Semantic Search**: Search through your documents using AI
    - 👁️ **Document Viewer**: Preview and manage your documents
    - 🗑️ **Document Management**: Delete individual documents or all documents
    - 🔒 **User Isolation**: Each user only sees their own documents
    
    **Supported File Types:**
    - PDF documents
    - Microsoft Word documents (.docx)
    - Plain text files (.txt)
    - HTML files (.html, .htm)
    - Web page content via URL
    """)
    
    st.markdown("---")

def render_demo_sidebar():
    """Render demo sidebar with information"""
    with st.sidebar:
        st.markdown("### 📚 Demo Information")
        st.markdown("""
        **Current User:** demo@example.com
        
        **Demo Features:**
        - Upload documents
        - View document library
        - Search documents
        - Delete documents
        
        **Note:** This is a demo environment. 
        In production, each user would have 
        their own isolated document space.
        """)
        
        st.markdown("---")
        st.markdown("### 🔧 Technical Details")
        st.markdown("""
        **Backend:**
        - Supabase with pgvector
        - LangChain for processing
        - Semantic embeddings
        
        **Processing:**
        - Text chunking
        - Vector embeddings
        - User-scoped storage
        """)

def main():
    """Main demo application"""
    # Initialize demo session
    initialize_demo_session()
    
    # Render demo interface
    render_demo_header()
    render_demo_sidebar()
    
    # Check if Supabase credentials are available
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_ANON_KEY"):
        st.error("""
        **Missing Supabase Configuration**
        
        To run this demo, you need to set up your Supabase credentials:
        
        1. Create a `.env` file in the project root
        2. Add your Supabase credentials:
           ```
           SUPABASE_URL=your_supabase_url
           SUPABASE_ANON_KEY=your_supabase_anon_key
           ```
        3. Restart the application
        
        See `STREAMLIT_SECRETS_SETUP.md` for detailed setup instructions.
        """)
        return
    
    try:
        # Initialize document management system
        document_manager = DocumentManager()
        document_interface = DocumentInterface(document_manager)
        
        # Get demo user ID
        user_id = st.session_state.demo_user_id
        
        # Render document management interface
        document_interface.render_document_page(user_id)
        
        # Show demo statistics
        st.markdown("---")
        st.subheader("📊 Demo Statistics")
        
        stats = document_manager.get_document_stats(user_id)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sources", stats['total_sources'])
        with col2:
            st.metric("Total Chunks", stats['total_chunks'])
        with col3:
            st.metric("File Types", len(stats['file_types']))
        with col4:
            st.metric("Messages", stats['message_count'])
        
        # Show file type breakdown
        if stats['file_types']:
            st.markdown("**File Type Distribution:**")
            for file_type, count in stats['file_types'].items():
                st.write(f"• **{file_type.upper()}**: {count} sources")
    
    except Exception as e:
        st.error(f"""
        **Demo Error**
        
        An error occurred while initializing the document management system:
        
        ```
        {str(e)}
        ```
        
        **Possible Solutions:**
        1. Check your Supabase credentials
        2. Ensure your database has the required tables
        3. Run the database migrations
        4. Check your internet connection
        
        See the setup documentation for help.
        """)
        
        # Show debug information
        with st.expander("🔧 Debug Information"):
            st.write("**Environment Variables:**")
            st.write(f"- SUPABASE_URL: {'✅ Set' if os.getenv('SUPABASE_URL') else '❌ Missing'}")
            st.write(f"- SUPABASE_ANON_KEY: {'✅ Set' if os.getenv('SUPABASE_ANON_KEY') else '❌ Missing'}")
            
            st.write("**Error Details:**")
            st.exception(e)

if __name__ == "__main__":
    main()