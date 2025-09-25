"""
Document Manager - User-scoped document management system
Handles document upload, storage, retrieval, and management with user isolation
"""

import streamlit as st
import os
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import tempfile
import shutil

from document_processor import DocumentProcessor, ProcessedDocument
from vector_retriever import VectorRetriever, Document
from database_utils import DatabaseUtils
from supabase import create_client


@dataclass
class DocumentInfo:
    """Document information for UI display"""
    id: str
    source: str
    content_preview: str
    chunk_count: int
    upload_date: datetime
    file_size: Optional[int] = None
    file_type: Optional[str] = None


@dataclass
class UploadResult:
    """Result of document upload operation"""
    success: bool
    documents_processed: int
    error_message: Optional[str] = None
    document_ids: List[str] = None


class DocumentManager:
    """Comprehensive document management system with user isolation"""
    
    def __init__(self, supabase_client=None, document_processor=None, vector_retriever=None, database_utils=None):
        """Initialize document manager with required components"""
        self.supabase_client = supabase_client or self._get_supabase_client()
        self.document_processor = document_processor or DocumentProcessor(self.supabase_client)
        self.vector_retriever = vector_retriever or VectorRetriever(self.supabase_client)
        self.database_utils = database_utils or DatabaseUtils(self.supabase_client)
    
    def _get_supabase_client(self):
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        return create_client(url, key)
    
    def upload_documents(
        self, 
        uploaded_files: List, 
        user_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> UploadResult:
        """
        Upload and process documents for a specific user
        
        Args:
            uploaded_files: List of Streamlit uploaded file objects
            user_id: User ID to associate documents with
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
            
        Returns:
            UploadResult with success status and details
        """
        try:
            if not uploaded_files:
                return UploadResult(
                    success=False,
                    documents_processed=0,
                    error_message="No files provided"
                )
            
            # Process uploaded files
            processed_docs = self.document_processor.process_uploaded_files(
                uploaded_files=uploaded_files,
                user_id=user_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            if not processed_docs:
                return UploadResult(
                    success=False,
                    documents_processed=0,
                    error_message="No documents could be processed"
                )
            
            # Store documents in vector database
            storage_success = self.document_processor.store_documents(processed_docs)
            
            if storage_success:
                document_ids = [doc.id for doc in processed_docs]
                return UploadResult(
                    success=True,
                    documents_processed=len(processed_docs),
                    document_ids=document_ids
                )
            else:
                return UploadResult(
                    success=False,
                    documents_processed=0,
                    error_message="Failed to store documents in database"
                )
                
        except Exception as e:
            return UploadResult(
                success=False,
                documents_processed=0,
                error_message=f"Upload failed: {str(e)}"
            )
    
    def upload_from_url(
        self,
        url: str,
        user_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> UploadResult:
        """
        Upload and process content from URL for a specific user
        
        Args:
            url: URL to extract content from
            user_id: User ID to associate documents with
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
            
        Returns:
            UploadResult with success status and details
        """
        try:
            # Process URL content
            processed_docs = self.document_processor.process_url_content(
                url=url,
                user_id=user_id,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            if not processed_docs:
                return UploadResult(
                    success=False,
                    documents_processed=0,
                    error_message="No content could be extracted from URL"
                )
            
            # Store documents in vector database
            storage_success = self.document_processor.store_documents(processed_docs)
            
            if storage_success:
                document_ids = [doc.id for doc in processed_docs]
                return UploadResult(
                    success=True,
                    documents_processed=len(processed_docs),
                    document_ids=document_ids
                )
            else:
                return UploadResult(
                    success=False,
                    documents_processed=0,
                    error_message="Failed to store documents in database"
                )
                
        except Exception as e:
            return UploadResult(
                success=False,
                documents_processed=0,
                error_message=f"URL upload failed: {str(e)}"
            )
    
    def get_user_documents(
        self, 
        user_id: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentInfo]:
        """
        Get all documents for a specific user with pagination
        
        Args:
            user_id: User ID to filter documents
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List of DocumentInfo objects
        """
        try:
            # Get raw documents from database
            raw_documents = self.vector_retriever.get_user_documents(
                user_id=user_id,
                limit=limit,
                offset=offset
            )
            
            # Group documents by source and convert to DocumentInfo
            document_groups = {}
            for doc in raw_documents:
                source = doc.source
                if source not in document_groups:
                    document_groups[source] = []
                document_groups[source].append(doc)
            
            # Create DocumentInfo objects
            document_infos = []
            for source, docs in document_groups.items():
                # Use the first document's metadata for display
                first_doc = docs[0]
                
                # Create content preview (first 200 characters)
                content_preview = first_doc.content[:200]
                if len(first_doc.content) > 200:
                    content_preview += "..."
                
                # Extract upload date from metadata or use current time
                upload_date = datetime.now()
                if first_doc.metadata and 'upload_timestamp' in first_doc.metadata:
                    try:
                        upload_date = datetime.fromtimestamp(
                            float(first_doc.metadata['upload_timestamp'])
                        )
                    except (ValueError, TypeError):
                        pass
                
                # Extract file info from metadata
                file_type = first_doc.metadata.get('file_type', 'unknown') if first_doc.metadata else 'unknown'
                
                doc_info = DocumentInfo(
                    id=first_doc.id,
                    source=source,
                    content_preview=content_preview,
                    chunk_count=len(docs),
                    upload_date=upload_date,
                    file_type=file_type
                )
                document_infos.append(doc_info)
            
            # Sort by upload date (newest first)
            document_infos.sort(key=lambda x: x.upload_date, reverse=True)
            
            return document_infos
            
        except Exception as e:
            st.error(f"Error retrieving user documents: {e}")
            return []
    
    def delete_document_by_source(self, user_id: str, source: str) -> bool:
        """
        Delete all document chunks for a specific source and user
        
        Args:
            user_id: User ID who owns the documents
            source: Source identifier (filename or URL)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.document_processor.delete_user_documents(
                user_id=user_id,
                source=source
            )
        except Exception as e:
            st.error(f"Error deleting document: {e}")
            return False
    
    def delete_all_user_documents(self, user_id: str) -> bool:
        """
        Delete all documents for a specific user
        
        Args:
            user_id: User ID whose documents to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.document_processor.delete_user_documents(user_id=user_id)
        except Exception as e:
            st.error(f"Error deleting all user documents: {e}")
            return False
    
    def get_document_count(self, user_id: str) -> int:
        """
        Get the total number of document chunks for a user
        
        Args:
            user_id: User ID to count documents for
            
        Returns:
            Number of document chunks
        """
        try:
            return self.vector_retriever.get_user_document_count(user_id)
        except Exception as e:
            st.error(f"Error getting document count: {e}")
            return 0
    
    def search_user_documents(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> List[Document]:
        """
        Search through user's documents using semantic similarity
        
        Args:
            user_id: User ID to filter documents
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching Document objects
        """
        try:
            return self.vector_retriever.similarity_search(
                query=query,
                user_id=user_id,
                k=limit
            )
        except Exception as e:
            st.error(f"Error searching documents: {e}")
            return []
    
    def get_document_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get statistics about user's documents
        
        Args:
            user_id: User ID to get stats for
            
        Returns:
            Dictionary with document statistics
        """
        try:
            # Get basic stats from database utils
            stats = self.database_utils.get_user_stats(user_id)
            
            # Get additional document-specific stats
            documents = self.get_user_documents(user_id, limit=1000)
            
            # Count by file type
            file_types = {}
            total_sources = len(documents)
            
            for doc in documents:
                file_type = doc.file_type or 'unknown'
                file_types[file_type] = file_types.get(file_type, 0) + 1
            
            return {
                'total_chunks': stats.get('document_count', 0),
                'total_sources': total_sources,
                'file_types': file_types,
                'message_count': stats.get('message_count', 0)
            }
            
        except Exception as e:
            st.error(f"Error getting document stats: {e}")
            return {
                'total_chunks': 0,
                'total_sources': 0,
                'file_types': {},
                'message_count': 0
            }