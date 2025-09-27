#!/usr/bin/env python3
"""
RAG Pipeline Integration Module
Provides a unified interface for RAG functionality with proper error handling
"""

import os
import sys
from typing import List, Dict, Any, Optional, Generator
import streamlit as st

class RAGPipelineManager:
    """Manages the complete RAG pipeline with error handling and fallbacks"""
    
    def __init__(self):
        self.document_processor = None
        self.vector_retriever = None
        self.context_builder = None
        self.rag_orchestrator = None
        self.embedding_model = None
        self._initialized = False
        self._initialization_error = None
    
    def initialize(self, lazy_load: bool = True) -> bool:
        """
        Initialize RAG components with lazy loading option
        
        Args:
            lazy_load: If True, only initialize when needed
            
        Returns:
            True if initialization successful, False otherwise
        """
        if self._initialized:
            return True
        
        if self._initialization_error and not lazy_load:
            return False
        
        try:
            # Import modules
            from document_processor import DocumentProcessor
            from vector_retriever import VectorRetriever
            from context_builder import ContextBuilder
            from rag_orchestrator import RAGOrchestrator, RAGConfig
            
            # Initialize components with error handling
            try:
                self.document_processor = DocumentProcessor()
                self.vector_retriever = VectorRetriever()
            except Exception as e:
                print(f"Warning: Database components not available: {e}")
                if not lazy_load:
                    return False
            
            # Initialize context builder (doesn't need database)
            self.context_builder = ContextBuilder()
            
            # Initialize RAG orchestrator
            config = RAGConfig(
                retrieval_k=3,
                similarity_threshold=0.2,
                fallback_to_llm_only=True
            )
            
            try:
                self.rag_orchestrator = RAGOrchestrator(
                    vector_retriever=self.vector_retriever,
                    context_builder=self.context_builder,
                    config=config
                )
            except Exception as e:
                print(f"Warning: RAG orchestrator initialization issue: {e}")
                if not lazy_load:
                    return False
            
            self._initialized = True
            return True
            
        except Exception as e:
            self._initialization_error = str(e)
            print(f"RAG Pipeline initialization failed: {e}")
            return False
    
    def process_documents(
        self, 
        uploaded_files: List, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Process uploaded documents
        
        Args:
            uploaded_files: List of uploaded file objects
            user_id: User ID for document association
            
        Returns:
            Dictionary with processing results
        """
        if not self.initialize():
            return {
                'success': False,
                'error': 'RAG pipeline not initialized',
                'documents_processed': 0
            }
        
        if not self.document_processor:
            return {
                'success': False,
                'error': 'Document processor not available (database required)',
                'documents_processed': 0
            }
        
        try:
            # Process files
            processed_docs = self.document_processor.process_uploaded_files(
                uploaded_files=uploaded_files,
                user_id=user_id
            )
            
            if not processed_docs:
                return {
                    'success': False,
                    'error': 'No documents could be processed',
                    'documents_processed': 0
                }
            
            # Store documents
            success = self.document_processor.store_documents(processed_docs)
            
            return {
                'success': success,
                'documents_processed': len(processed_docs),
                'error': None if success else 'Failed to store documents'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Document processing failed: {str(e)}',
                'documents_processed': 0
            }
    
    def query_documents(
        self, 
        query: str, 
        user_id: str,
        model_type: str = "fast",
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Query documents using RAG pipeline
        
        Args:
            query: User query
            user_id: User ID for document filtering
            model_type: Model type to use
            stream: Whether to stream response
            
        Returns:
            Query results or error information
        """
        if not self.initialize():
            return {
                'success': False,
                'error': 'RAG pipeline not initialized',
                'response': 'Sorry, the document search system is not available.'
            }
        
        if not self.rag_orchestrator:
            return {
                'success': False,
                'error': 'RAG orchestrator not available',
                'response': 'Sorry, the document search system is not available.'
            }
        
        try:
            if stream:
                # Return generator for streaming
                return {
                    'success': True,
                    'stream': self.rag_orchestrator.stream_query(
                        query=query,
                        user_id=user_id,
                        model_type=model_type
                    )
                }
            else:
                # Regular query
                result = self.rag_orchestrator.process_query(
                    query=query,
                    user_id=user_id,
                    model_type=model_type
                )
                
                return {
                    'success': result.success,
                    'response': result.response,
                    'context_used': result.context_used,
                    'documents_retrieved': len(result.documents_retrieved),
                    'error': result.error_message
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Query processing failed: {str(e)}',
                'response': 'Sorry, I encountered an error while searching your documents.'
            }
    
    def get_user_document_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's documents"""
        if not self.initialize():
            return {'document_count': 0, 'error': 'RAG pipeline not initialized'}
        
        if not self.vector_retriever:
            return {'document_count': 0, 'error': 'Database not available'}
        
        try:
            count = self.vector_retriever.get_user_document_count(user_id)
            return {'document_count': count, 'error': None}
        except Exception as e:
            return {'document_count': 0, 'error': str(e)}
    
    def delete_user_documents(self, user_id: str, source: Optional[str] = None) -> bool:
        """Delete user documents"""
        if not self.initialize():
            return False
        
        if not self.document_processor:
            return False
        
        try:
            return self.document_processor.delete_user_documents(user_id, source)
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of RAG pipeline components"""
        status = {
            'overall': 'unknown',
            'components': {},
            'errors': []
        }
        
        # Check initialization
        init_success = self.initialize(lazy_load=True)
        status['components']['initialization'] = 'ok' if init_success else 'error'
        
        if not init_success:
            status['errors'].append(f'Initialization failed: {self._initialization_error}')
        
        # Check individual components
        components = [
            ('document_processor', self.document_processor),
            ('vector_retriever', self.vector_retriever),
            ('context_builder', self.context_builder),
            ('rag_orchestrator', self.rag_orchestrator)
        ]
        
        for name, component in components:
            if component is not None:
                status['components'][name] = 'ok'
            else:
                status['components'][name] = 'unavailable'
                status['errors'].append(f'{name} not available')
        
        # Determine overall status
        if all(s in ['ok', 'unavailable'] for s in status['components'].values()):
            if any(s == 'unavailable' for s in status['components'].values()):
                status['overall'] = 'degraded'
            else:
                status['overall'] = 'healthy'
        else:
            status['overall'] = 'error'
        
        return status

# Global instance
_rag_pipeline = None

def get_rag_pipeline() -> RAGPipelineManager:
    """Get global RAG pipeline instance"""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipelineManager()
    return _rag_pipeline

def test_rag_pipeline():
    """Test RAG pipeline functionality"""
    print("🔧 Testing RAG Pipeline Integration")
    print("=" * 40)
    
    pipeline = get_rag_pipeline()
    
    # Test health check
    health = pipeline.health_check()
    print(f"Health Status: {health['overall']}")
    
    for component, status in health['components'].items():
        print(f"  {component}: {status}")
    
    if health['errors']:
        print("Errors:")
        for error in health['errors']:
            print(f"  - {error}")
    
    return health['overall'] in ['healthy', 'degraded']

if __name__ == "__main__":
    success = test_rag_pipeline()
    sys.exit(0 if success else 1)