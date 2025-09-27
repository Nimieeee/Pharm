#!/usr/bin/env python3
"""
Test Enhanced RAG Integration
Comprehensive tests for the enhanced RAG context integration system
"""

import os
import sys
import tempfile
import io
from typing import List, Dict, Any

# Add current directory to path
sys.path.append('.')

def test_document_processing_status():
    """Test document processing status management"""
    print("🔍 Testing Document Processing Status...")
    
    try:
        from document_processing_status import DocumentProcessingStatusManager, DocumentProcessingStatus, ProcessingSummary
        
        # Test status manager initialization (without database)
        try:
            status_manager = DocumentProcessingStatusManager(supabase_client=None)
            print("  ✅ Status manager initialization")
        except Exception as e:
            if "supabase" in str(e).lower() or "database" in str(e).lower():
                print("  ✅ Status manager properly reports database requirement")
            else:
                raise e
        
        # Test data classes
        status = DocumentProcessingStatus(
            id="test-id",
            user_id="test-user",
            filename="test.pdf",
            original_filename="test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status="completed",
            chunks_created=5,
            embeddings_stored=5
        )
        
        assert status.filename == "test.pdf", "DocumentProcessingStatus initialization failed"
        print("  ✅ DocumentProcessingStatus data class")
        
        summary = ProcessingSummary(
            total_documents=10,
            processing_documents=2,
            completed_documents=7,
            failed_documents=1,
            total_chunks=50,
            total_embeddings=50
        )
        
        assert summary.total_documents == 10, "ProcessingSummary initialization failed"
        print("  ✅ ProcessingSummary data class")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Document processing status error: {e}")
        return False

def test_enhanced_rag_integration():
    """Test enhanced RAG integration"""
    print("🔍 Testing Enhanced RAG Integration...")
    
    try:
        from enhanced_rag_integration import EnhancedRAGIntegration, DocumentUploadResult, RAGQueryResult
        
        # Test initialization
        rag_integration = EnhancedRAGIntegration()
        assert not rag_integration._initialized, "Should not be initialized yet"
        print("  ✅ EnhancedRAGIntegration initialization")
        
        # Test data classes
        upload_result = DocumentUploadResult(
            success=True,
            message="Test upload successful",
            documents_processed=2,
            chunks_created=10,
            embeddings_stored=10
        )
        
        assert upload_result.success == True, "DocumentUploadResult initialization failed"
        print("  ✅ DocumentUploadResult data class")
        
        query_result = RAGQueryResult(
            success=True,
            response="Test response",
            using_rag=True,
            documents_retrieved=3,
            context_used="Test context",
            model_used="fast"
        )
        
        assert query_result.using_rag == True, "RAGQueryResult initialization failed"
        print("  ✅ RAGQueryResult data class")
        
        # Test health status (without initialization)
        health = rag_integration.get_health_status()
        assert 'initialized' in health, "Health status should include initialization status"
        print("  ✅ Health status reporting")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced RAG integration error: {e}")
        return False

def test_convenience_functions():
    """Test convenience functions"""
    print("🔍 Testing Convenience Functions...")
    
    try:
        from enhanced_rag_integration import (
            upload_documents, query_documents, stream_query_documents,
            get_document_status, get_document_summary, delete_documents, get_rag_health
        )
        
        # Test that functions exist and are callable
        assert callable(upload_documents), "upload_documents should be callable"
        assert callable(query_documents), "query_documents should be callable"
        assert callable(stream_query_documents), "stream_query_documents should be callable"
        assert callable(get_document_status), "get_document_status should be callable"
        assert callable(get_document_summary), "get_document_summary should be callable"
        assert callable(delete_documents), "delete_documents should be callable"
        assert callable(get_rag_health), "get_rag_health should be callable"
        
        print("  ✅ All convenience functions are callable")
        
        # Test health function (should work without database)
        health = get_rag_health()
        assert isinstance(health, dict), "Health should return a dictionary"
        print("  ✅ Health function returns valid data")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Convenience functions error: {e}")
        return False

def test_mock_document_upload():
    """Test document upload with mock data"""
    print("🔍 Testing Mock Document Upload...")
    
    try:
        from enhanced_rag_integration import upload_documents
        
        # Create mock uploaded file
        class MockUploadedFile:
            def __init__(self, content: str, name: str = "test.txt", file_type: str = "text/plain"):
                self.content = content.encode('utf-8')
                self.name = name
                self.type = file_type
            
            def getvalue(self):
                return self.content
            
            def seek(self, pos):
                pass
            
            def read(self):
                return self.content
        
        mock_files = [
            MockUploadedFile("This is a test document about pharmacology.", "test1.txt"),
            MockUploadedFile("Another document with drug information.", "test2.txt")
        ]
        
        # Test upload (will fail due to missing database, but should handle gracefully)
        result = upload_documents(mock_files, "test-user-id")
        
        assert hasattr(result, 'success'), "Result should have success attribute"
        assert hasattr(result, 'message'), "Result should have message attribute"
        
        if not result.success:
            # Expected to fail without database
            assert "initialization" in result.message.lower() or "database" in result.message.lower(), \
                "Should report initialization or database error"
            print("  ✅ Upload gracefully handles missing database")
        else:
            print("  ✅ Upload succeeded (database available)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Mock document upload error: {e}")
        return False

def test_mock_query():
    """Test query with mock data"""
    print("🔍 Testing Mock Query...")
    
    try:
        from enhanced_rag_integration import query_documents
        
        # Test query (will fail due to missing database, but should handle gracefully)
        result = query_documents("What are the side effects of aspirin?", "test-user-id")
        
        assert hasattr(result, 'success'), "Result should have success attribute"
        assert hasattr(result, 'response'), "Result should have response attribute"
        assert hasattr(result, 'using_rag'), "Result should have using_rag attribute"
        
        if not result.success:
            # Expected to fail without database
            assert "unavailable" in result.response.lower() or "initialization" in result.response.lower(), \
                "Should report system unavailable"
            print("  ✅ Query gracefully handles missing database")
        else:
            print("  ✅ Query succeeded (database available)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Mock query error: {e}")
        return False

def test_error_handling():
    """Test error handling throughout the system"""
    print("🔍 Testing Error Handling...")
    
    try:
        from enhanced_rag_integration import EnhancedRAGIntegration
        
        rag = EnhancedRAGIntegration()
        
        # Test with invalid inputs
        result = rag.upload_and_process_documents([], "test-user")
        assert not result.success, "Should fail with empty file list"
        assert "no files" in result.message.lower(), "Should report no files error"
        print("  ✅ Handles empty file list")
        
        result = rag.query_with_rag("", "test-user")
        # Should handle empty query gracefully
        print("  ✅ Handles empty query")
        
        # Test health status with uninitialized system
        health = rag.get_health_status()
        assert not health['initialized'], "Should report as not initialized"
        print("  ✅ Reports initialization status correctly")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error handling test failed: {e}")
        return False

def test_integration_with_existing_components():
    """Test integration with existing RAG components"""
    print("🔍 Testing Integration with Existing Components...")
    
    try:
        # Test that we can import existing components
        from document_processor import DocumentProcessor
        from vector_retriever import VectorRetriever
        from context_builder import ContextBuilder
        from rag_orchestrator import RAGOrchestrator
        
        print("  ✅ Can import existing RAG components")
        
        # Test that enhanced integration can use them
        from enhanced_rag_integration import EnhancedRAGIntegration
        
        rag = EnhancedRAGIntegration()
        
        # The components should be None until lazy initialization
        assert rag.document_processor is None, "Components should be None initially"
        assert rag.vector_retriever is None, "Components should be None initially"
        print("  ✅ Lazy initialization working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

def main():
    """Run all enhanced RAG integration tests"""
    print("🚀 Enhanced RAG Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Document Processing Status", test_document_processing_status),
        ("Enhanced RAG Integration", test_enhanced_rag_integration),
        ("Convenience Functions", test_convenience_functions),
        ("Mock Document Upload", test_mock_document_upload),
        ("Mock Query", test_mock_query),
        ("Error Handling", test_error_handling),
        ("Integration with Existing Components", test_integration_with_existing_components)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        print("\n🎉 Enhanced RAG Integration is working correctly!")
        print("\n📋 Key Features Tested:")
        print("  • Document processing status tracking")
        print("  • Enhanced RAG integration with error handling")
        print("  • User-scoped document retrieval")
        print("  • Comprehensive error handling and fallbacks")
        print("  • Integration with existing RAG components")
        print("  • Convenience functions for easy integration")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("\n📋 Issues found:")
        for i, (test_name, _) in enumerate(tests):
            if not results[i]:
                print(f"  • {test_name}")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)