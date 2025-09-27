"""
Document Management UI Components
Provides user interface for document upload, management, and viewing
Enhanced with comprehensive error handling and user feedback.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import io
import logging

from document_manager import DocumentManager, DocumentInfo, UploadResult
from ui_error_handler import UIErrorHandler, UIErrorType, UIErrorContext, with_ui_error_handling

logger = logging.getLogger(__name__)


class DocumentUploadInterface:
    """Interface for document upload functionality"""
    
    def __init__(self, document_manager: DocumentManager):
        self.document_manager = document_manager
        self.ui_error_handler = UIErrorHandler()
    
    def render_upload_section(self, user_id: str) -> Optional[UploadResult]:
        """
        Render document upload interface
        
        Args:
            user_id: Current user ID
            
        Returns:
            UploadResult if upload was attempted, None otherwise
        """
        st.subheader("📁 Upload Documents")
        
        # Create tabs for different upload methods
        tab1, tab2 = st.tabs(["📄 File Upload", "🌐 URL Upload"])
        
        upload_result = None
        
        with tab1:
            upload_result = self._render_file_upload(user_id)
        
        with tab2:
            url_result = self._render_url_upload(user_id)
            if url_result:
                upload_result = url_result
        
        return upload_result
    
    def _render_file_upload(self, user_id: str) -> Optional[UploadResult]:
        """Render file upload interface"""
        st.markdown("Upload PDF, DOCX, TXT, or HTML files to add to your knowledge base.")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose files",
            type=['pdf', 'docx', 'txt', 'html', 'htm'],
            accept_multiple_files=True,
            key="document_uploader"
        )
        
        if not uploaded_files:
            st.info("Select files to upload")
            return None
        
        # Display selected files
        st.write(f"**Selected files ({len(uploaded_files)}):**")
        for file in uploaded_files:
            file_size = len(file.getvalue()) if hasattr(file, 'getvalue') else 0
            file_size_mb = file_size / (1024 * 1024)
            st.write(f"• {file.name} ({file_size_mb:.2f} MB)")
        
        # Upload settings
        with st.expander("⚙️ Upload Settings"):
            chunk_size = st.slider(
                "Chunk Size (characters)",
                min_value=500,
                max_value=2000,
                value=1000,
                step=100,
                help="Size of text chunks for processing. Smaller chunks provide more precise retrieval."
            )
            
            chunk_overlap = st.slider(
                "Chunk Overlap (characters)",
                min_value=50,
                max_value=500,
                value=200,
                step=50,
                help="Overlap between chunks to maintain context."
            )
        
        # Upload button
        if st.button("🚀 Upload Files", type="primary", use_container_width=True):
            return self._handle_file_upload_with_error_handling(
                uploaded_files, user_id, chunk_size, chunk_overlap
            )
        
        return None
    
    def _render_url_upload(self, user_id: str) -> Optional[UploadResult]:
        """Render URL upload interface"""
        st.markdown("Extract content from web pages and add to your knowledge base.")
        
        # URL input
        url = st.text_input(
            "Enter URL",
            placeholder="https://example.com/article",
            help="Enter a URL to extract and process its content"
        )
        
        if not url:
            st.info("Enter a URL to extract content")
            return None
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            st.warning("Please enter a valid URL starting with http:// or https://")
            return None
        
        # Upload settings
        with st.expander("⚙️ Processing Settings"):
            chunk_size = st.slider(
                "Chunk Size (characters)",
                min_value=500,
                max_value=2000,
                value=1000,
                step=100,
                key="url_chunk_size"
            )
            
            chunk_overlap = st.slider(
                "Chunk Overlap (characters)",
                min_value=50,
                max_value=500,
                value=200,
                step=50,
                key="url_chunk_overlap"
            )
        
        # Upload button
        if st.button("🌐 Extract and Upload", type="primary", use_container_width=True):
            return self._handle_url_upload_with_error_handling(
                url, user_id, chunk_size, chunk_overlap
            )
        
        return None
    
    def _handle_file_upload_with_error_handling(self, uploaded_files, user_id: str, 
                                               chunk_size: int, chunk_overlap: int) -> Optional[UploadResult]:
        """Handle file upload with comprehensive error handling"""
        try:
            with st.spinner("Processing and uploading documents..."):
                upload_result = self.document_manager.upload_documents(
                    uploaded_files=uploaded_files,
                    user_id=user_id,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
                if upload_result.success:
                    st.success(f"✅ Successfully uploaded {upload_result.documents_processed} document chunks!")
                    st.balloons()
                    
                    # Show processing details
                    if hasattr(upload_result, 'processing_details') and upload_result.processing_details:
                        with st.expander("📊 Processing Details"):
                            for detail in upload_result.processing_details:
                                st.write(f"• {detail}")
                else:
                    # Handle upload failure with detailed error feedback
                    context = UIErrorContext(
                        user_id=user_id,
                        action="file_upload",
                        component="DocumentUploadInterface",
                        additional_data={
                            'file_count': len(uploaded_files),
                            'chunk_size': chunk_size,
                            'error_message': upload_result.error_message
                        }
                    )
                    
                    # Create a mock exception for error handling
                    error = Exception(upload_result.error_message or "Upload failed")
                    error_result = self.ui_error_handler.handle_document_processing_error(error, context)
                    self.ui_error_handler.display_error_with_actions(error_result)
                
                return upload_result
                
        except Exception as e:
            logger.error(f"Error during file upload for user {user_id}: {e}")
            context = UIErrorContext(
                user_id=user_id,
                action="file_upload",
                component="DocumentUploadInterface",
                additional_data={'file_count': len(uploaded_files)}
            )
            error_result = self.ui_error_handler.handle_document_processing_error(e, context)
            self.ui_error_handler.display_error_with_actions(error_result)
            
            # Return failed result
            return UploadResult(
                success=False,
                documents_processed=0,
                error_message=str(e)
            )
    
    def _handle_url_upload_with_error_handling(self, url: str, user_id: str, 
                                              chunk_size: int, chunk_overlap: int) -> Optional[UploadResult]:
        """Handle URL upload with comprehensive error handling"""
        try:
            with st.spinner("Extracting content from URL..."):
                upload_result = self.document_manager.upload_from_url(
                    url=url,
                    user_id=user_id,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
                if upload_result.success:
                    st.success(f"✅ Successfully processed {upload_result.documents_processed} chunks from URL!")
                    st.balloons()
                    
                    # Show URL processing details
                    with st.expander("🌐 URL Processing Details"):
                        st.write(f"**Source:** {url}")
                        st.write(f"**Chunks Created:** {upload_result.documents_processed}")
                        if hasattr(upload_result, 'processing_details') and upload_result.processing_details:
                            for detail in upload_result.processing_details:
                                st.write(f"• {detail}")
                else:
                    # Handle URL processing failure
                    context = UIErrorContext(
                        user_id=user_id,
                        action="url_upload",
                        component="DocumentUploadInterface",
                        additional_data={
                            'url': url,
                            'chunk_size': chunk_size,
                            'error_message': upload_result.error_message
                        }
                    )
                    
                    # Create specific error based on failure type
                    error_message = upload_result.error_message or "URL processing failed"
                    if "network" in error_message.lower() or "connection" in error_message.lower():
                        error = ConnectionError(error_message)
                    elif "invalid" in error_message.lower() or "not found" in error_message.lower():
                        error = ValueError(error_message)
                    else:
                        error = Exception(error_message)
                    
                    error_result = self.ui_error_handler.handle_document_processing_error(error, context)
                    self.ui_error_handler.display_error_with_actions(error_result)
                
                return upload_result
                
        except Exception as e:
            logger.error(f"Error during URL upload for user {user_id}: {e}")
            context = UIErrorContext(
                user_id=user_id,
                action="url_upload",
                component="DocumentUploadInterface",
                additional_data={'url': url}
            )
            error_result = self.ui_error_handler.handle_document_processing_error(e, context)
            self.ui_error_handler.display_error_with_actions(error_result)
            
            # Return failed result
            return UploadResult(
                success=False,
                documents_processed=0,
                error_message=str(e)
            )


class DocumentManagementInterface:
    """Interface for managing existing documents"""
    
    def __init__(self, document_manager: DocumentManager):
        self.document_manager = document_manager
    
    def render_document_library(self, user_id: str) -> None:
        """
        Render document library with management options
        
        Args:
            user_id: Current user ID
        """
        st.subheader("📚 Document Library")
        
        # Get document statistics
        stats = self.document_manager.get_document_stats(user_id)
        
        # Display stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sources", stats['total_sources'])
        with col2:
            st.metric("Total Chunks", stats['total_chunks'])
        with col3:
            st.metric("Messages Sent", stats['message_count'])
        
        # Display file type breakdown
        if stats['file_types']:
            st.markdown("**File Types:**")
            for file_type, count in stats['file_types'].items():
                st.write(f"• {file_type.upper()}: {count} sources")
        
        st.markdown("---")
        
        # Get user documents
        documents = self.document_manager.get_user_documents(user_id, limit=100)
        
        if not documents:
            st.info("No documents uploaded yet. Use the upload section above to add documents.")
            return
        
        # Search functionality
        search_query = st.text_input(
            "🔍 Search your documents",
            placeholder="Enter keywords to search...",
            help="Search through your document content using semantic similarity"
        )
        
        if search_query:
            self._render_search_results(user_id, search_query)
        else:
            self._render_document_list(user_id, documents)
    
    def _render_search_results(self, user_id: str, query: str) -> None:
        """Render search results"""
        st.markdown(f"**Search results for:** *{query}*")
        
        with st.spinner("Searching documents..."):
            search_results = self.document_manager.search_user_documents(
                user_id=user_id,
                query=query,
                limit=10
            )
        
        if not search_results:
            st.info("No matching documents found.")
            return
        
        for i, doc in enumerate(search_results):
            with st.expander(f"📄 {doc.source} (Similarity: {doc.similarity:.2f})"):
                st.write("**Content:**")
                st.write(doc.content)
                
                if doc.metadata:
                    st.write("**Metadata:**")
                    st.json(doc.metadata)
    
    def _render_document_list(self, user_id: str, documents: List[DocumentInfo]) -> None:
        """Render list of user documents with management options"""
        st.markdown(f"**Your Documents ({len(documents)}):**")
        
        # Bulk actions
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🗑️ Delete All", type="secondary", use_container_width=True):
                if st.session_state.get('confirm_delete_all', False):
                    with st.spinner("Deleting all documents..."):
                        if self.document_manager.delete_all_user_documents(user_id):
                            st.success("All documents deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete documents")
                    st.session_state.confirm_delete_all = False
                else:
                    st.session_state.confirm_delete_all = True
                    st.warning("Click again to confirm deletion of ALL documents")
        
        # Document list
        for doc in documents:
            self._render_document_item(user_id, doc)
    
    def _render_document_item(self, user_id: str, doc: DocumentInfo) -> None:
        """Render individual document item with actions"""
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # Document info
                st.markdown(f"**📄 {doc.source}**")
                st.caption(f"Uploaded: {doc.upload_date.strftime('%Y-%m-%d %H:%M')}")
                st.caption(f"Type: {doc.file_type.upper()} • Chunks: {doc.chunk_count}")
                
                # Content preview
                with st.expander("Preview"):
                    st.write(doc.content_preview)
            
            with col2:
                # View button
                if st.button("👁️ View", key=f"view_{doc.id}", use_container_width=True):
                    self._show_document_details(user_id, doc.source)
            
            with col3:
                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{doc.id}", use_container_width=True):
                    confirm_key = f"confirm_delete_{doc.id}"
                    if st.session_state.get(confirm_key, False):
                        with st.spinner(f"Deleting {doc.source}..."):
                            if self.document_manager.delete_document_by_source(user_id, doc.source):
                                st.success(f"Deleted {doc.source}")
                                st.rerun()
                            else:
                                st.error("Failed to delete document")
                        st.session_state[confirm_key] = False
                    else:
                        st.session_state[confirm_key] = True
                        st.warning("Click again to confirm")
            
            st.markdown("---")
    
    def _show_document_details(self, user_id: str, source: str) -> None:
        """Show detailed view of a document"""
        st.subheader(f"📄 Document Details: {source}")
        
        # Get all chunks for this source
        with st.spinner("Loading document details..."):
            # Search for all chunks from this source
            all_docs = self.document_manager.get_user_documents(user_id, limit=1000)
            source_docs = [doc for doc in all_docs if doc.source == source]
        
        if not source_docs:
            st.error("Document not found")
            return
        
        # Display document info
        doc = source_docs[0]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Chunks", doc.chunk_count)
        with col2:
            st.metric("File Type", doc.file_type.upper())
        with col3:
            st.metric("Upload Date", doc.upload_date.strftime('%Y-%m-%d'))
        
        # Show content preview
        st.markdown("**Content Preview:**")
        st.text_area("", value=doc.content_preview, height=200, disabled=True)
        
        # Back button
        if st.button("← Back to Library"):
            st.rerun()


class DocumentInterface:
    """Main document management interface combining upload and management"""
    
    def __init__(self, document_manager: DocumentManager):
        self.document_manager = document_manager
        self.upload_interface = DocumentUploadInterface(document_manager)
        self.management_interface = DocumentManagementInterface(document_manager)
    
    def render_document_page(self, user_id: str) -> None:
        """
        Render complete document management page
        
        Args:
            user_id: Current user ID
        """
        st.title("📚 Document Management")
        st.markdown("Upload and manage your pharmacology documents for enhanced AI assistance.")
        
        # Upload section
        upload_result = self.upload_interface.render_upload_section(user_id)
        
        # If upload was successful, refresh the page to show new documents
        if upload_result and upload_result.success:
            st.rerun()
        
        st.markdown("---")
        
        # Document library section
        self.management_interface.render_document_library(user_id)
    
    def render_sidebar_summary(self, user_id: str) -> None:
        """
        Render document summary in sidebar
        
        Args:
            user_id: Current user ID
        """
        st.sidebar.markdown("### 📚 Documents")
        
        # Get quick stats
        stats = self.document_manager.get_document_stats(user_id)
        
        st.sidebar.metric("Sources", stats['total_sources'])
        st.sidebar.metric("Chunks", stats['total_chunks'])
        
        # Quick actions
        if st.sidebar.button("📁 Manage Documents", use_container_width=True):
            st.session_state.show_document_page = True
            st.rerun()