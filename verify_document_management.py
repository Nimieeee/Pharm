"""
Verification script for document management functionality
Tests the core components and integration without requiring full database setup
"""

import os
import tempfile
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Import components to verify
from document_manager import DocumentManager, DocumentInfo, UploadResult
from document_processor import ProcessedDocument
from vector_retriever import Document


def test_document_manager_initialization():
    """Test DocumentManager can be initialized with mocked components"""
    print("Testing DocumentManager initialization...")
    
    # Create mock components
    mock_supabase = Mock()
    mock_processor = Mock()
    mock_retriever = Mock()
    mock_db_utils = Mock()
    
    # Initialize DocumentManager with mocked components
    doc_manager = DocumentManager(
        supabase_client=mock_supabase,
        document_processor=mock_processor,
        vector_retriever=mock_retriever,
        database_utils=mock_db_utils
    )
    
    # Verify initialization
    assert doc_manager.supabase_client == mock_supabase
    assert doc_manager.document_processor == mock_processor
    assert doc_manager.vector_retriever == mock_retriever
    assert doc_manager.database_utils == mock_db_utils
    
    print("✅ DocumentManager initialization successful")


def test_upload_result_structure():
    """Test UploadResult data structure"""
    print("Testing UploadResult structure...")
    
    # Test successful result
    success_result = UploadResult(
        success=True,
        documents_processed=5,
        document_ids=["doc1", "doc2", "doc3", "doc4", "doc5"]
    )
    
    assert success_result.success is True
    assert success_result.documents_processed == 5
    assert len(success_result.document_ids) == 5
    assert success_result.error_message is None
    
    # Test failure result
    failure_result = UploadResult(
        success=False,
        documents_processed=0,
        error_message="Upload failed"
    )
    
    assert failure_result.success is False
    assert failure_result.documents_processed == 0
    assert failure_result.error_message == "Upload failed"
    assert failure_result.document_ids is None
    
    print("✅ UploadResult structure verification successful")


def test_document_info_structure():
    """Test DocumentInfo data structure"""
    print("Testing DocumentInfo structure...")
    
    doc_info = DocumentInfo(
        id="test-doc-123",
        source="test_document.pdf",
        content_preview="This is a preview of the document content...",
        chunk_count=3,
        upload_date=datetime.now(),
        file_size=1024,
        file_type="pdf"
    )
    
    assert doc_info.id == "test-doc-123"
    assert doc_info.source == "test_document.pdf"
    assert doc_info.chunk_count == 3
    assert doc_info.file_type == "pdf"
    assert doc_info.file_size == 1024
    assert isinstance(doc_info.upload_date, datetime)
    
    print("✅ DocumentInfo structure verification successful")


def test_document_upload_workflow():
    """Test document upload workflow with mocked components"""
    print("Testing document upload workflow...")
    
    # Create mock components
    mock_supabase = Mock()
    mock_processor = Mock()
    mock_retriever = Mock()
    mock_db_utils = Mock()
    
    # Configure mock processor
    mock_processed_docs = [
        ProcessedDocument(
            id="doc1",
            user_id="test-user",
            content="Test content chunk 1",
            source="test.pdf",
            metadata={"chunk_index": 0}
        ),
        ProcessedDocument(
            id="doc2",
            user_id="test-user",
            content="Test content chunk 2",
            source="test.pdf",
            metadata={"chunk_index": 1}
        )
    ]
    
    mock_processor.process_uploaded_files.return_value = mock_processed_docs
    mock_processor.store_documents.return_value = True
    
    # Initialize DocumentManager
    doc_manager = DocumentManager(
        supabase_client=mock_supabase,
        document_processor=mock_processor,
        vector_retriever=mock_retriever,
        database_utils=mock_db_utils
    )
    
    # Mock uploaded files
    mock_files = [Mock(name="test.pdf")]
    
    # Test upload
    result = doc_manager.upload_documents(
        uploaded_files=mock_files,
        user_id="test-user"
    )
    
    # Verify result
    assert result.success is True
    assert result.documents_processed == 2
    assert result.document_ids == ["doc1", "doc2"]
    
    # Verify processor was called
    mock_processor.process_uploaded_files.assert_called_once()
    mock_processor.store_documents.assert_called_once_with(mock_processed_docs)
    
    print("✅ Document upload workflow verification successful")


def test_document_retrieval_workflow():
    """Test document retrieval workflow with mocked components"""
    print("Testing document retrieval workflow...")
    
    # Create mock components
    mock_supabase = Mock()
    mock_processor = Mock()
    mock_retriever = Mock()
    mock_db_utils = Mock()
    
    # Configure mock retriever
    mock_raw_docs = [
        Document(
            id="doc1",
            content="Test content 1 for pharmacology research",
            source="test1.pdf",
            metadata={
                "chunk_index": 0,
                "file_type": "pdf",
                "upload_timestamp": str(datetime.now().timestamp())
            }
        ),
        Document(
            id="doc2",
            content="Test content 2 for pharmacology research",
            source="test1.pdf",
            metadata={
                "chunk_index": 1,
                "file_type": "pdf",
                "upload_timestamp": str(datetime.now().timestamp())
            }
        ),
        Document(
            id="doc3",
            content="Different document about drug interactions",
            source="test2.txt",
            metadata={
                "chunk_index": 0,
                "file_type": "txt",
                "upload_timestamp": str(datetime.now().timestamp())
            }
        )
    ]
    
    mock_retriever.get_user_documents.return_value = mock_raw_docs
    
    # Initialize DocumentManager
    doc_manager = DocumentManager(
        supabase_client=mock_supabase,
        document_processor=mock_processor,
        vector_retriever=mock_retriever,
        database_utils=mock_db_utils
    )
    
    # Test retrieval
    documents = doc_manager.get_user_documents("test-user")
    
    # Verify results
    assert len(documents) == 2  # Two unique sources
    
    # Find documents by source
    pdf_doc = next((doc for doc in documents if doc.source == "test1.pdf"), None)
    txt_doc = next((doc for doc in documents if doc.source == "test2.txt"), None)
    
    assert pdf_doc is not None
    assert pdf_doc.chunk_count == 2
    assert pdf_doc.file_type == "pdf"
    
    assert txt_doc is not None
    assert txt_doc.chunk_count == 1
    assert txt_doc.file_type == "txt"
    
    # Verify retriever was called
    mock_retriever.get_user_documents.assert_called_once_with(
        user_id="test-user",
        limit=100,
        offset=0
    )
    
    print("✅ Document retrieval workflow verification successful")


def test_document_search_workflow():
    """Test document search workflow with mocked components"""
    print("Testing document search workflow...")
    
    # Create mock components
    mock_supabase = Mock()
    mock_processor = Mock()
    mock_retriever = Mock()
    mock_db_utils = Mock()
    
    # Configure mock retriever for search
    mock_search_results = [
        Document(
            id="doc1",
            content="Pharmacology content about drug interactions and mechanisms",
            source="pharmacology_textbook.pdf",
            metadata={"chapter": "drug_interactions"},
            similarity=0.89
        ),
        Document(
            id="doc2",
            content="Clinical pharmacology research on drug metabolism",
            source="research_paper.pdf",
            metadata={"type": "research"},
            similarity=0.76
        )
    ]
    
    mock_retriever.similarity_search.return_value = mock_search_results
    
    # Initialize DocumentManager
    doc_manager = DocumentManager(
        supabase_client=mock_supabase,
        document_processor=mock_processor,
        vector_retriever=mock_retriever,
        database_utils=mock_db_utils
    )
    
    # Test search
    results = doc_manager.search_user_documents(
        user_id="test-user",
        query="drug interactions",
        limit=5
    )
    
    # Verify results
    assert len(results) == 2
    assert results[0].similarity == 0.89
    assert results[1].similarity == 0.76
    assert "drug interactions" in results[0].content
    assert "drug metabolism" in results[1].content
    
    # Verify retriever was called
    mock_retriever.similarity_search.assert_called_once_with(
        query="drug interactions",
        user_id="test-user",
        k=5
    )
    
    print("✅ Document search workflow verification successful")


def test_document_deletion_workflow():
    """Test document deletion workflow with mocked components"""
    print("Testing document deletion workflow...")
    
    # Create mock components
    mock_supabase = Mock()
    mock_processor = Mock()
    mock_retriever = Mock()
    mock_db_utils = Mock()
    
    # Configure mock processor for deletion
    mock_processor.delete_user_documents.return_value = True
    
    # Initialize DocumentManager
    doc_manager = DocumentManager(
        supabase_client=mock_supabase,
        document_processor=mock_processor,
        vector_retriever=mock_retriever,
        database_utils=mock_db_utils
    )
    
    # Test deletion by source
    result = doc_manager.delete_document_by_source(
        user_id="test-user",
        source="test_document.pdf"
    )
    
    # Verify result
    assert result is True
    
    # Verify processor was called
    mock_processor.delete_user_documents.assert_called_once_with(
        user_id="test-user",
        source="test_document.pdf"
    )
    
    print("✅ Document deletion workflow verification successful")


def test_document_stats_workflow():
    """Test document statistics workflow with mocked components"""
    print("Testing document statistics workflow...")
    
    # Create mock components
    mock_supabase = Mock()
    mock_processor = Mock()
    mock_retriever = Mock()
    mock_db_utils = Mock()
    
    # Configure mock database utils
    mock_db_utils.get_user_stats.return_value = {
        'document_count': 15,
        'message_count': 42
    }
    
    # Initialize DocumentManager
    doc_manager = DocumentManager(
        supabase_client=mock_supabase,
        document_processor=mock_processor,
        vector_retriever=mock_retriever,
        database_utils=mock_db_utils
    )
    
    # Mock get_user_documents method
    mock_documents = [
        DocumentInfo(
            id="doc1",
            source="test1.pdf",
            content_preview="Preview 1",
            chunk_count=3,
            upload_date=datetime.now(),
            file_type="pdf"
        ),
        DocumentInfo(
            id="doc2",
            source="test2.txt",
            content_preview="Preview 2",
            chunk_count=2,
            upload_date=datetime.now(),
            file_type="txt"
        ),
        DocumentInfo(
            id="doc3",
            source="test3.docx",
            content_preview="Preview 3",
            chunk_count=1,
            upload_date=datetime.now(),
            file_type="docx"
        )
    ]
    
    # Mock the get_user_documents method
    doc_manager.get_user_documents = Mock(return_value=mock_documents)
    
    # Test stats retrieval
    stats = doc_manager.get_document_stats("test-user")
    
    # Verify results
    assert stats['total_chunks'] == 15
    assert stats['total_sources'] == 3
    assert stats['message_count'] == 42
    assert stats['file_types'] == {'pdf': 1, 'txt': 1, 'docx': 1}
    
    print("✅ Document statistics workflow verification successful")


def run_all_tests():
    """Run all verification tests"""
    print("🧪 Starting Document Management Verification Tests")
    print("=" * 60)
    
    try:
        test_document_manager_initialization()
        test_upload_result_structure()
        test_document_info_structure()
        test_document_upload_workflow()
        test_document_retrieval_workflow()
        test_document_search_workflow()
        test_document_deletion_workflow()
        test_document_stats_workflow()
        
        print("=" * 60)
        print("🎉 All Document Management Verification Tests Passed!")
        print("\n✅ Core functionality verified:")
        print("   • Document upload and processing")
        print("   • User-scoped document retrieval")
        print("   • Semantic document search")
        print("   • Document deletion")
        print("   • Statistics and analytics")
        print("   • Data structure integrity")
        
        return True
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)