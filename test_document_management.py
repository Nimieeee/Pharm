"""
Test suite for document management functionality
Tests document upload, storage, retrieval, and user isolation
"""

import pytest
import os
import tempfile
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List

# Import components to test
from document_manager import DocumentManager, DocumentInfo, UploadResult
from document_processor import DocumentProcessor, ProcessedDocument
from vector_retriever import VectorRetriever, Document


class TestDocumentManager:
    """Test cases for DocumentManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_supabase_client = Mock()
        self.document_manager = DocumentManager(self.mock_supabase_client)
        self.test_user_id = "test-user-123"
    
    def test_initialization(self):
        """Test DocumentManager initialization"""
        assert self.document_manager.supabase_client == self.mock_supabase_client
        assert isinstance(self.document_manager.document_processor, DocumentProcessor)
        assert isinstance(self.document_manager.vector_retriever, VectorRetriever)
    
    @patch('document_manager.DocumentProcessor')
    def test_upload_documents_success(self, mock_processor_class):
        """Test successful document upload"""
        # Mock processed documents
        mock_processed_docs = [
            ProcessedDocument(
                id="doc1",
                user_id=self.test_user_id,
                content="Test content 1",
                source="test1.pdf",
                metadata={"chunk_index": 0}
            ),
            ProcessedDocument(
                id="doc2",
                user_id=self.test_user_id,
                content="Test content 2",
                source="test1.pdf",
                metadata={"chunk_index": 1}
            )
        ]
        
        # Mock processor methods
        mock_processor = mock_processor_class.return_value
        mock_processor.process_uploaded_files.return_value = mock_processed_docs
        mock_processor.store_documents.return_value = True
        
        # Mock uploaded files
        mock_files = [Mock(name="test1.pdf")]
        
        # Test upload
        result = self.document_manager.upload_documents(
            uploaded_files=mock_files,
            user_id=self.test_user_id
        )
        
        # Verify result
        assert result.success is True
        assert result.documents_processed == 2
        assert result.document_ids == ["doc1", "doc2"]
        
        # Verify processor was called correctly
        mock_processor.process_uploaded_files.assert_called_once_with(
            uploaded_files=mock_files,
            user_id=self.test_user_id,
            chunk_size=1000,
            chunk_overlap=200
        )
        mock_processor.store_documents.assert_called_once_with(mock_processed_docs)
    
    @patch('document_manager.DocumentProcessor')
    def test_upload_documents_no_files(self, mock_processor_class):
        """Test upload with no files provided"""
        result = self.document_manager.upload_documents(
            uploaded_files=[],
            user_id=self.test_user_id
        )
        
        assert result.success is False
        assert result.documents_processed == 0
        assert result.error_message == "No files provided"
    
    @patch('document_manager.DocumentProcessor')
    def test_upload_documents_processing_failure(self, mock_processor_class):
        """Test upload when document processing fails"""
        mock_processor = mock_processor_class.return_value
        mock_processor.process_uploaded_files.return_value = []
        
        mock_files = [Mock(name="test1.pdf")]
        
        result = self.document_manager.upload_documents(
            uploaded_files=mock_files,
            user_id=self.test_user_id
        )
        
        assert result.success is False
        assert result.documents_processed == 0
        assert result.error_message == "No documents could be processed"
    
    @patch('document_manager.DocumentProcessor')
    def test_upload_documents_storage_failure(self, mock_processor_class):
        """Test upload when storage fails"""
        mock_processed_docs = [
            ProcessedDocument(
                id="doc1",
                user_id=self.test_user_id,
                content="Test content",
                source="test1.pdf",
                metadata={}
            )
        ]
        
        mock_processor = mock_processor_class.return_value
        mock_processor.process_uploaded_files.return_value = mock_processed_docs
        mock_processor.store_documents.return_value = False
        
        mock_files = [Mock(name="test1.pdf")]
        
        result = self.document_manager.upload_documents(
            uploaded_files=mock_files,
            user_id=self.test_user_id
        )
        
        assert result.success is False
        assert result.documents_processed == 0
        assert result.error_message == "Failed to store documents in database"
    
    @patch('document_manager.VectorRetriever')
    def test_get_user_documents(self, mock_retriever_class):
        """Test retrieving user documents"""
        # Mock raw documents from database
        mock_raw_docs = [
            Document(
                id="doc1",
                content="Test content 1 for pharmacology",
                source="test1.pdf",
                metadata={
                    "chunk_index": 0,
                    "file_type": "pdf",
                    "upload_timestamp": str(datetime.now().timestamp())
                }
            ),
            Document(
                id="doc2",
                content="Test content 2 for pharmacology",
                source="test1.pdf",
                metadata={
                    "chunk_index": 1,
                    "file_type": "pdf",
                    "upload_timestamp": str(datetime.now().timestamp())
                }
            ),
            Document(
                id="doc3",
                content="Different document content",
                source="test2.txt",
                metadata={
                    "chunk_index": 0,
                    "file_type": "txt",
                    "upload_timestamp": str(datetime.now().timestamp())
                }
            )
        ]
        
        mock_retriever = mock_retriever_class.return_value
        mock_retriever.get_user_documents.return_value = mock_raw_docs
        
        # Test retrieval
        documents = self.document_manager.get_user_documents(self.test_user_id)
        
        # Verify results
        assert len(documents) == 2  # Two unique sources
        
        # Check first document (test1.pdf)
        pdf_doc = next(doc for doc in documents if doc.source == "test1.pdf")
        assert pdf_doc.chunk_count == 2
        assert pdf_doc.file_type == "pdf"
        assert "Test content 1" in pdf_doc.content_preview
        
        # Check second document (test2.txt)
        txt_doc = next(doc for doc in documents if doc.source == "test2.txt")
        assert txt_doc.chunk_count == 1
        assert txt_doc.file_type == "txt"
        assert "Different document" in txt_doc.content_preview
        
        # Verify retriever was called correctly
        mock_retriever.get_user_documents.assert_called_once_with(
            user_id=self.test_user_id,
            limit=100,
            offset=0
        )
    
    @patch('document_manager.DocumentProcessor')
    def test_delete_document_by_source(self, mock_processor_class):
        """Test deleting documents by source"""
        mock_processor = mock_processor_class.return_value
        mock_processor.delete_user_documents.return_value = True
        
        result = self.document_manager.delete_document_by_source(
            user_id=self.test_user_id,
            source="test1.pdf"
        )
        
        assert result is True
        mock_processor.delete_user_documents.assert_called_once_with(
            user_id=self.test_user_id,
            source="test1.pdf"
        )
    
    @patch('document_manager.VectorRetriever')
    def test_search_user_documents(self, mock_retriever_class):
        """Test searching user documents"""
        mock_search_results = [
            Document(
                id="doc1",
                content="Pharmacology content about drug interactions",
                source="test1.pdf",
                metadata={},
                similarity=0.85
            )
        ]
        
        mock_retriever = mock_retriever_class.return_value
        mock_retriever.similarity_search.return_value = mock_search_results
        
        results = self.document_manager.search_user_documents(
            user_id=self.test_user_id,
            query="drug interactions",
            limit=5
        )
        
        assert len(results) == 1
        assert results[0].similarity == 0.85
        assert "drug interactions" in results[0].content
        
        mock_retriever.similarity_search.assert_called_once_with(
            query="drug interactions",
            user_id=self.test_user_id,
            k=5
        )
    
    def test_get_document_stats(self):
        """Test getting document statistics"""
        # Mock database utils
        mock_stats = {
            'document_count': 10,
            'message_count': 25
        }
        self.document_manager.database_utils.get_user_stats = Mock(return_value=mock_stats)
        
        # Mock document list
        mock_documents = [
            DocumentInfo(
                id="doc1",
                source="test1.pdf",
                content_preview="Preview",
                chunk_count=2,
                upload_date=datetime.now(),
                file_type="pdf"
            ),
            DocumentInfo(
                id="doc2",
                source="test2.txt",
                content_preview="Preview",
                chunk_count=1,
                upload_date=datetime.now(),
                file_type="txt"
            )
        ]
        self.document_manager.get_user_documents = Mock(return_value=mock_documents)
        
        stats = self.document_manager.get_document_stats(self.test_user_id)
        
        assert stats['total_chunks'] == 10
        assert stats['total_sources'] == 2
        assert stats['message_count'] == 25
        assert stats['file_types'] == {'pdf': 1, 'txt': 1}


class TestDocumentUserIsolation:
    """Test user isolation in document management"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_supabase_client = Mock()
        self.document_manager = DocumentManager(self.mock_supabase_client)
        self.user1_id = "user1-123"
        self.user2_id = "user2-456"
    
    @patch('document_manager.VectorRetriever')
    def test_user_document_isolation(self, mock_retriever_class):
        """Test that users can only see their own documents"""
        # Mock documents for user1
        user1_docs = [
            Document(
                id="user1-doc1",
                content="User 1 content",
                source="user1-file.pdf",
                metadata={"user_id": self.user1_id}
            )
        ]
        
        # Mock documents for user2
        user2_docs = [
            Document(
                id="user2-doc1",
                content="User 2 content",
                source="user2-file.pdf",
                metadata={"user_id": self.user2_id}
            )
        ]
        
        mock_retriever = mock_retriever_class.return_value
        
        # Configure mock to return different results based on user_id
        def mock_get_user_documents(user_id, limit=100, offset=0):
            if user_id == self.user1_id:
                return user1_docs
            elif user_id == self.user2_id:
                return user2_docs
            else:
                return []
        
        mock_retriever.get_user_documents.side_effect = mock_get_user_documents
        
        # Test user1 documents
        user1_results = self.document_manager.get_user_documents(self.user1_id)
        assert len(user1_results) == 1
        assert user1_results[0].source == "user1-file.pdf"
        
        # Test user2 documents
        user2_results = self.document_manager.get_user_documents(self.user2_id)
        assert len(user2_results) == 1
        assert user2_results[0].source == "user2-file.pdf"
        
        # Verify isolation - user1 should not see user2's documents
        assert user1_results[0].source != user2_results[0].source
    
    @patch('document_manager.VectorRetriever')
    def test_search_isolation(self, mock_retriever_class):
        """Test that search results are isolated by user"""
        mock_retriever = mock_retriever_class.return_value
        
        # Configure mock to return user-specific results
        def mock_similarity_search(query, user_id, k=5, similarity_threshold=0.1):
            if user_id == self.user1_id:
                return [Document(
                    id="user1-result",
                    content=f"User 1 result for {query}",
                    source="user1-doc.pdf",
                    metadata={}
                )]
            elif user_id == self.user2_id:
                return [Document(
                    id="user2-result",
                    content=f"User 2 result for {query}",
                    source="user2-doc.pdf",
                    metadata={}
                )]
            else:
                return []
        
        mock_retriever.similarity_search.side_effect = mock_similarity_search
        
        # Test search for both users
        user1_results = self.document_manager.search_user_documents(
            user_id=self.user1_id,
            query="pharmacology"
        )
        user2_results = self.document_manager.search_user_documents(
            user_id=self.user2_id,
            query="pharmacology"
        )
        
        # Verify results are user-specific
        assert len(user1_results) == 1
        assert len(user2_results) == 1
        assert user1_results[0].id != user2_results[0].id
        assert "User 1" in user1_results[0].content
        assert "User 2" in user2_results[0].content


def test_document_upload_integration():
    """Integration test for document upload workflow"""
    # This would require actual Supabase connection for full integration testing
    # For now, we'll test the workflow with mocks
    
    with patch('document_manager.create_client') as mock_create_client:
        mock_client = Mock()
        mock_create_client.return_value = mock_client
        
        # Mock environment variables
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'test-url',
            'SUPABASE_ANON_KEY': 'test-key'
        }):
            document_manager = DocumentManager()
            
            # Mock file upload
            mock_file = Mock()
            mock_file.name = "test.pdf"
            mock_file.getvalue.return_value = b"Test PDF content"
            
            # This would test the full workflow if we had real implementations
            # For now, we verify the manager was initialized correctly
            assert document_manager.supabase_client == mock_client


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])