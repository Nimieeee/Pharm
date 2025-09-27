# rag_ui_integration.py
import streamlit as st
from typing import List, Dict, Any, Optional
from enhanced_rag_integration import (
    upload_documents, query_documents, stream_query_documents,
    get_document_status, get_document_summary, delete_documents, get_rag_health
)
from document_processing_status import DocumentProcessingStatus

def show_document_upload_interface(user_id: str) -> bool:
    """
    Show document upload interface with processing status
    
    Args:
        user_id: Current user ID
        
    Returns:
        True if documents were uploaded, False otherwise
    """
    st.subheader("📄 Document Upload")
    
    # Show current document summary
    summary = get_document_summary(user_id)
    
    if summary['total_documents'] > 0:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Documents", summary['total_documents'])
        with col2:
            st.metric("Completed", summary['completed_documents'])
        with col3:
            st.metric("Processing", summary.get('processing_documents', 0))
        with col4:
            st.metric("Failed", summary['failed_documents'])
        
        if summary['total_chunks'] > 0:
            st.info(f"📊 Total chunks: {summary['total_chunks']} | Embeddings: {summary['total_embeddings']}")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Upload documents for AI context",
        type=['pdf', 'txt', 'docx', 'html', 'htm'],
        accept_multiple_files=True,
        help="Upload documents to enhance AI responses with your specific content"
    )
    
    # Upload settings
    with st.expander("⚙️ Upload Settings"):
        col1, col2 = st.columns(2)
        with col1:
            chunk_size = st.slider("Chunk Size", 500, 2000, 1000, 100,
                                 help="Size of text chunks for processing")
        with col2:
            chunk_overlap = st.slider("Chunk Overlap", 50, 500, 200, 50,
                                    help="Overlap between chunks for better context")
    
    # Process upload
    if uploaded_files and st.button("📤 Upload and Process Documents", type="primary"):
        with st.spinner("Processing documents..."):
            result = upload_documents(
                uploaded_files, 
                user_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            if result.success:
                st.success(result.message)
                if result.documents_processed > 0:
                    st.balloons()
                return True
            else:
                st.error(f"Upload failed: {result.message}")
                if result.error_details:
                    with st.expander("Error Details"):
                        st.code(result.error_details)
                return False
    
    return False

def show_document_status_interface(user_id: str):
    """
    Show document processing status interface
    
    Args:
        user_id: Current user ID
    """
    st.subheader("📊 Document Processing Status")
    
    # Get processing status
    status_list = get_document_status(user_id)
    
    if not status_list:
        st.info("No documents uploaded yet. Use the upload interface above to add documents.")
        return
    
    # Show status table
    status_data = []
    for status in status_list:
        status_data.append({
            "Filename": status.original_filename,
            "Status": status.status.title(),
            "Chunks": status.chunks_created,
            "Embeddings": status.embeddings_stored,
            "File Size": f"{status.file_size / 1024:.1f} KB" if status.file_size else "Unknown"
        })
    
    st.dataframe(status_data, use_container_width=True)
    
    # Show failed documents with error details
    failed_docs = [s for s in status_list if s.status == 'failed']
    if failed_docs:
        st.warning(f"⚠️ {len(failed_docs)} document(s) failed to process")
        
        with st.expander("View Failed Documents"):
            for doc in failed_docs:
                st.error(f"**{doc.original_filename}**: {doc.error_message or 'Unknown error'}")
    
    # Document management
    if st.button("🗑️ Delete All Documents", type="secondary"):
        if st.session_state.get('confirm_delete', False):
            with st.spinner("Deleting documents..."):
                success = delete_documents(user_id)
                if success:
                    st.success("All documents deleted successfully")
                    st.rerun()
                else:
                    st.error("Failed to delete documents")
            st.session_state.confirm_delete = False
        else:
            st.session_state.confirm_delete = True
            st.warning("Click again to confirm deletion of all documents")

def show_rag_health_interface():
    """Show RAG system health interface"""
    st.subheader("🔧 RAG System Health")
    
    health = get_rag_health()
    
    # Overall status
    if health['initialized']:
        st.success("✅ RAG System Initialized")
    else:
        st.error("❌ RAG System Not Initialized")
        if health['initialization_error']:
            st.error(f"Error: {health['initialization_error']}")
    
    # Component status
    if 'components' in health and health['components']:
        st.write("**Component Status:**")
        components = health['components']
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("📄 Document Processor:", "✅" if components.get('document_processor') else "❌")
            st.write("🔍 Vector Retriever:", "✅" if components.get('vector_retriever') else "❌")
            st.write("🧠 Context Builder:", "✅" if components.get('context_builder') else "❌")
        
        with col2:
            st.write("🤖 RAG Orchestrator:", "✅" if components.get('rag_orchestrator') else "❌")
            st.write("📊 Status Manager:", "✅" if components.get('status_manager') else "❌")
    
    # Refresh button
    if st.button("🔄 Refresh Status"):
        st.rerun()

def show_rag_query_interface(user_id: str, query: str, model_type: str = "fast") -> Optional[str]:
    """
    Show RAG query interface and process query
    
    Args:
        user_id: Current user ID
        query: User query
        model_type: Model type to use
        
    Returns:
        Response string if successful, None otherwise
    """
    if not query.strip():
        return None
    
    # Check if user has documents
    summary = get_document_summary(user_id)
    has_documents = summary['completed_documents'] > 0
    
    if not has_documents:
        st.info("💡 Upload documents to get more specific answers based on your content!")
    
    # Process query
    try:
        # Use streaming for better UX
        response_container = st.empty()
        full_response = ""
        
        for chunk in stream_query_documents(query, user_id, model_type):
            if isinstance(chunk, str):
                full_response += chunk
                response_container.markdown(full_response + "▌")
            else:
                # Final result
                response_container.markdown(full_response)
                
                # Show RAG metadata
                if hasattr(chunk, 'using_rag') and chunk.using_rag:
                    st.success(f"✨ Enhanced with {chunk.documents_retrieved} relevant document(s)")
                elif has_documents:
                    st.info("💭 Using general knowledge (no relevant documents found)")
                
                return full_response
        
        # Fallback if streaming doesn't work as expected
        response_container.markdown(full_response)
        return full_response
        
    except Exception as e:
        st.error(f"Query processing failed: {str(e)}")
        return None

def show_document_management_sidebar(user_id: str):
    """
    Show document management in sidebar
    
    Args:
        user_id: Current user ID
    """
    with st.sidebar:
        st.header("📚 Document Management")
        
        # Quick summary
        summary = get_document_summary(user_id)
        
        if summary['total_documents'] > 0:
            st.metric("Documents", summary['completed_documents'])
            st.metric("Chunks", summary['total_chunks'])
            
            # Processing status
            if summary.get('processing_documents', 0) > 0:
                st.warning(f"⏳ {summary['processing_documents']} processing...")
            
            if summary['failed_documents'] > 0:
                st.error(f"❌ {summary['failed_documents']} failed")
        else:
            st.info("No documents uploaded")
        
        # Quick upload
        uploaded_file = st.file_uploader(
            "Quick Upload",
            type=['pdf', 'txt', 'docx'],
            help="Upload a single document"
        )
        
        if uploaded_file and st.button("Upload", key="sidebar_upload"):
            with st.spinner("Processing..."):
                result = upload_documents([uploaded_file], user_id)
                if result.success:
                    st.success("✅ Uploaded!")
                    st.rerun()
                else:
                    st.error("❌ Failed")

def show_rag_context_info(user_id: str, query: str):
    """
    Show information about RAG context for a query
    
    Args:
        user_id: Current user ID
        query: User query
    """
    if not query.strip():
        return
    
    with st.expander("🔍 RAG Context Information"):
        summary = get_document_summary(user_id)
        
        st.write(f"**Available Documents:** {summary['completed_documents']}")
        st.write(f"**Total Chunks:** {summary['total_chunks']}")
        
        if summary['completed_documents'] > 0:
            # Simulate context retrieval info (would need actual retrieval to show real context)
            st.write("**Context Strategy:**")
            st.write("- Searching through your uploaded documents")
            st.write("- Using semantic similarity matching")
            st.write("- Retrieving top 3 most relevant chunks")
            st.write("- Fallback to general knowledge if no relevant content found")
        else:
            st.write("**No documents available for context enhancement**")
            st.write("Upload documents to get more specific and relevant answers!")

# Convenience function for full RAG interface
def show_full_rag_interface(user_id: str):
    """
    Show complete RAG interface with all components
    
    Args:
        user_id: Current user ID
    """
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "📊 Status", "🔧 Health"])
    
    with tab1:
        show_document_upload_interface(user_id)
    
    with tab2:
        show_document_status_interface(user_id)
    
    with tab3:
        show_rag_health_interface()