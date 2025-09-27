# enhanced_rag_integration.py
import os
import uuid
from typing import List, Dict, Any, Optional, Generator, Tuple
from dataclasses import dataclass
import streamlit as st

# Import RAG components
from document_processor import DocumentProcessor, ProcessedDocument
from vector_retriever import VectorRetriever, Document
from context_builder import ContextBuilder, ContextConfig
from rag_orchestrator import RAGOrchestrator, RAGConfig, RAGResponse
from document_processing_status import DocumentProcessingStatusManager, DocumentProcessingStatus
from embeddings import get_embeddings

@dataclass
class DocumentUploadResult:
    """Result of document upload operation"""
    success: bool
    message: str
    documents_processed: int = 0
    chunks_created: int = 0
    embeddings_stored: int = 0
    processing_record_id: Optional[str] = None
    error_details: Optional[str] = None

@dataclass
class RAGQueryResult:
    """Result of RAG query operation"""
    success: bool
    response: str
    using_rag: bool
    documents_retrieved: int = 0
    context_used: str = ""
    model_used: str = ""
    error_message: Optional[str] = None

class EnhancedRAGIntegration:
    """Enhanced RAG integration with comprehensive error handling and user feedback"""
    
    def __init__(self):
        self.document_processor = None
        self.vector_retriever = None
        self.context_builder = None
        self.rag_orchestrator = None
        self.status_manager = None
        self._initialized = False
        self._initialization_error = None
    
    def _lazy_initialize(self) -> bool:
        """Lazy initialization of RAG components"""
        if self._initialized:
            return self._initialization_error is None
        
        try:
            # Initialize components
            self.document_processor = DocumentProcessor()
            self.vector_retriever = VectorRetriever()
            self.context_builder = ContextBuilder()
            self.status_manager = DocumentProcessingStatusManager()
            
            # Initialize RAG orchestrator with optimized config
            rag_config = RAGConfig(
                retrieval_k=3,
                similarity_threshold=0.2,
                fallback_to_llm_only=True,
                max_retries=2
            )
            
            self.rag_orchestrator = RAGOrchestrator(
                vector_retriever=self.vector_retriever,
                context_builder=self.context_builder,
                config=rag_config
            )
            
            self._initialized = True
            self._initialization_error = None
            return True
            
        except Exception as e:
            self._initialization_error = str(e)
            print(f"RAG initialization error: {e}")
            return False
    
    def upload_and_process_documents(
        self, 
        uploaded_files: List, 
        user_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> DocumentUploadResult:
        """
        Upload and process documents with comprehensive error handling and status tracking
        
        Args:
            uploaded_files: List of uploaded file objects
            user_id: User ID for document association
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            DocumentUploadResult with processing details
        """
        if not self._lazy_initialize():
            return DocumentUploadResult(
                success=False,
                message=f"RAG system initialization failed: {self._initialization_error}",
                error_details=self._initialization_error
            )
        
        if not uploaded_files:
            return DocumentUploadResult(
                success=False,
                message="No files provided for processing"
            )
        
        total_processed = 0
        total_chunks = 0
        total_embeddings = 0
        processing_records = []
        
        try:
            for uploaded_file in uploaded_files:
                # Create processing record
                try:
                    file_size = len(uploaded_file.getvalue()) if hasattr(uploaded_file, 'getvalue') else 0
                    mime_type = getattr(uploaded_file, 'type', 'application/octet-stream')
                    filename = getattr(uploaded_file, 'name', f'upload_{uuid.uuid4().hex[:8]}')
                    
                    record_id = self.status_manager.create_processing_record(
                        user_id=user_id,
                        filename=filename,
                        original_filename=filename,
                        file_size=file_size,
                        mime_type=mime_type
                    )
                    processing_records.append(record_id)
                    
                    # Update status to processing
                    self.status_manager.update_status(record_id, 'processing')
                    
                except Exception as e:
                    print(f"Error creating processing record: {e}")
                    record_id = None
                
                try:
                    # Process the document
                    processed_docs = self.document_processor.process_uploaded_files(
                        uploaded_files=[uploaded_file],
                        user_id=user_id,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                    
                    if processed_docs:
                        # Store documents with embeddings
                        storage_success = self.document_processor.store_documents(processed_docs)
                        
                        if storage_success:
                            total_processed += 1
                            total_chunks += len(processed_docs)
                            total_embeddings += len(processed_docs)  # Assuming 1 embedding per chunk
                            
                            # Update status to completed
                            if record_id:
                                self.status_manager.update_status(
                                    record_id, 
                                    'completed',
                                    chunks_created=len(processed_docs),
                                    embeddings_stored=len(processed_docs)
                                )
                        else:
                            # Update status to failed
                            if record_id:
                                self.status_manager.update_status(
                                    record_id, 
                                    'failed',
                                    error_message="Failed to store document embeddings"
                                )
                    else:
                        # Update status to failed
                        if record_id:
                            self.status_manager.update_status(
                                record_id, 
                                'failed',
                                error_message="Failed to process document content"
                            )
                
                except Exception as e:
                    print(f"Error processing file {getattr(uploaded_file, 'name', 'unknown')}: {e}")
                    if record_id:
                        self.status_manager.update_status(
                            record_id, 
                            'failed',
                            error_message=str(e)
                        )
            
            if total_processed > 0:
                return DocumentUploadResult(
                    success=True,
                    message=f"Successfully processed {total_processed} document(s), created {total_chunks} chunks with {total_embeddings} embeddings",
                    documents_processed=total_processed,
                    chunks_created=total_chunks,
                    embeddings_stored=total_embeddings,
                    processing_record_id=processing_records[0] if processing_records else None
                )
            else:
                return DocumentUploadResult(
                    success=False,
                    message="Failed to process any documents. Please check file formats and try again.",
                    error_details="No documents were successfully processed"
                )
                
        except Exception as e:
            return DocumentUploadResult(
                success=False,
                message=f"Document processing failed: {str(e)}",
                error_details=str(e)
            )
    
    def query_with_rag(
        self, 
        query: str, 
        user_id: str,
        model_type: str = "fast",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> RAGQueryResult:
        """
        Query with RAG integration and comprehensive error handling
        
        Args:
            query: User query
            user_id: User ID for document filtering
            model_type: Model type ("fast" or "premium")
            conversation_history: Optional conversation history
            
        Returns:
            RAGQueryResult with response and metadata
        """
        if not self._lazy_initialize():
            return RAGQueryResult(
                success=False,
                response=f"RAG system unavailable: {self._initialization_error}",
                using_rag=False,
                error_message=self._initialization_error
            )
        
        try:
            # Process query with RAG
            rag_response = self.rag_orchestrator.process_query(
                query=query,
                user_id=user_id,
                model_type=model_type,
                conversation_history=conversation_history
            )
            
            if rag_response.success:
                return RAGQueryResult(
                    success=True,
                    response=rag_response.response,
                    using_rag=len(rag_response.documents_retrieved) > 0,
                    documents_retrieved=len(rag_response.documents_retrieved),
                    context_used=rag_response.context_used,
                    model_used=rag_response.model_used
                )
            else:
                return RAGQueryResult(
                    success=False,
                    response=rag_response.response,
                    using_rag=False,
                    error_message=rag_response.error_message
                )
                
        except Exception as e:
            return RAGQueryResult(
                success=False,
                response=f"Query processing failed: {str(e)}",
                using_rag=False,
                error_message=str(e)
            )
    
    def stream_query_with_rag(
        self, 
        query: str, 
        user_id: str,
        model_type: str = "fast",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Generator[str, None, RAGQueryResult]:
        """
        Stream query with RAG integration
        
        Args:
            query: User query
            user_id: User ID for document filtering
            model_type: Model type ("fast" or "premium")
            conversation_history: Optional conversation history
            
        Yields:
            Response chunks
            
        Returns:
            Final RAGQueryResult with metadata
        """
        if not self._lazy_initialize():
            error_msg = f"RAG system unavailable: {self._initialization_error}"
            yield error_msg
            return RAGQueryResult(
                success=False,
                response=error_msg,
                using_rag=False,
                error_message=self._initialization_error
            )
        
        try:
            # Stream query with RAG
            response_chunks = []
            
            for chunk in self.rag_orchestrator.stream_query(
                query=query,
                user_id=user_id,
                model_type=model_type,
                conversation_history=conversation_history
            ):
                if isinstance(chunk, str):
                    response_chunks.append(chunk)
                    yield chunk
                else:
                    # Final result
                    full_response = "".join(response_chunks)
                    return RAGQueryResult(
                        success=chunk.success if hasattr(chunk, 'success') else True,
                        response=full_response,
                        using_rag=len(chunk.documents_retrieved) > 0 if hasattr(chunk, 'documents_retrieved') else False,
                        documents_retrieved=len(chunk.documents_retrieved) if hasattr(chunk, 'documents_retrieved') else 0,
                        context_used=chunk.context_used if hasattr(chunk, 'context_used') else "",
                        model_used=chunk.model_used if hasattr(chunk, 'model_used') else model_type
                    )
            
            # If we get here, create a result from the chunks
            full_response = "".join(response_chunks)
            return RAGQueryResult(
                success=True,
                response=full_response,
                using_rag=True,  # Assume RAG was used if we got here
                model_used=model_type
            )
            
        except Exception as e:
            error_msg = f"Streaming query failed: {str(e)}"
            yield error_msg
            return RAGQueryResult(
                success=False,
                response=error_msg,
                using_rag=False,
                error_message=str(e)
            )
    
    def get_user_document_status(self, user_id: str) -> List[DocumentProcessingStatus]:
        """Get document processing status for user"""
        if not self._lazy_initialize():
            return []
        
        try:
            return self.status_manager.get_user_processing_status(user_id)
        except Exception as e:
            print(f"Error getting document status: {e}")
            return []
    
    def get_user_document_summary(self, user_id: str) -> Dict[str, Any]:
        """Get document processing summary for user"""
        if not self._lazy_initialize():
            return {
                'total_documents': 0,
                'completed_documents': 0,
                'failed_documents': 0,
                'total_chunks': 0,
                'total_embeddings': 0
            }
        
        try:
            summary = self.status_manager.get_processing_summary(user_id)
            return {
                'total_documents': summary.total_documents,
                'processing_documents': summary.processing_documents,
                'completed_documents': summary.completed_documents,
                'failed_documents': summary.failed_documents,
                'total_chunks': summary.total_chunks,
                'total_embeddings': summary.total_embeddings
            }
        except Exception as e:
            print(f"Error getting document summary: {e}")
            return {
                'total_documents': 0,
                'completed_documents': 0,
                'failed_documents': 0,
                'total_chunks': 0,
                'total_embeddings': 0
            }
    
    def delete_user_documents(self, user_id: str, source: Optional[str] = None) -> bool:
        """Delete user documents"""
        if not self._lazy_initialize():
            return False
        
        try:
            return self.document_processor.delete_user_documents(user_id, source)
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get RAG system health status"""
        status = {
            'initialized': self._initialized,
            'initialization_error': self._initialization_error,
            'components': {}
        }
        
        if self._initialized:
            status['components'] = {
                'document_processor': self.document_processor is not None,
                'vector_retriever': self.vector_retriever is not None,
                'context_builder': self.context_builder is not None,
                'rag_orchestrator': self.rag_orchestrator is not None,
                'status_manager': self.status_manager is not None
            }
        
        return status

# Global instance
enhanced_rag = EnhancedRAGIntegration()

# Convenience functions for easy integration
def upload_documents(uploaded_files: List, user_id: str, **kwargs) -> DocumentUploadResult:
    """Upload and process documents"""
    return enhanced_rag.upload_and_process_documents(uploaded_files, user_id, **kwargs)

def query_documents(query: str, user_id: str, model_type: str = "fast", **kwargs) -> RAGQueryResult:
    """Query documents with RAG"""
    return enhanced_rag.query_with_rag(query, user_id, model_type, **kwargs)

def stream_query_documents(query: str, user_id: str, model_type: str = "fast", **kwargs):
    """Stream query documents with RAG"""
    return enhanced_rag.stream_query_with_rag(query, user_id, model_type, **kwargs)

def get_document_status(user_id: str) -> List[DocumentProcessingStatus]:
    """Get document processing status"""
    return enhanced_rag.get_user_document_status(user_id)

def get_document_summary(user_id: str) -> Dict[str, Any]:
    """Get document processing summary"""
    return enhanced_rag.get_user_document_summary(user_id)

def delete_documents(user_id: str, source: Optional[str] = None) -> bool:
    """Delete user documents"""
    return enhanced_rag.delete_user_documents(user_id, source)

def get_rag_health() -> Dict[str, Any]:
    """Get RAG system health"""
    return enhanced_rag.get_health_status()