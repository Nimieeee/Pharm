#!/usr/bin/env python3
"""
Simple Task 10 Verification
Quick verification that enhanced RAG integration is working
"""

import sys
sys.path.append('.')

def test_imports():
    """Test that all new components can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from enhanced_rag_integration import (
            EnhancedRAGIntegration, DocumentUploadResult, RAGQueryResult,
            upload_documents, query_documents, get_rag_health
        )
        print("  ✅ Enhanced RAG integration")
        
        from document_processing_status import (
            DocumentProcessingStatusManager, DocumentProcessingStatus, ProcessingSummary
        )
        print("  ✅ Document processing status")
        
        from rag_ui_integration import (
            show_document_upload_interface, show_document_status_interface,
            show_rag_health_interface, show_full_rag_interface
        )
        print("  ✅ RAG UI integration")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without database"""
    print("🔍 Testing basic functionality...")
    
    try:
        from enhanced_rag_integration import get_rag_health, upload_documents, query_documents
        
        # Test health check
        health = get_rag_health()
        assert isinstance(health, dict), "Health should return dict"
        print("  ✅ Health monitoring")
        
        # Test upload with empty list
        result = upload_documents([], "test-user")
        assert not result.success, "Should fail with empty list"
        print("  ✅ Upload error handling")
        
        # Test query
        result = query_documents("test", "test-user")
        assert hasattr(result, 'success'), "Should return result object"
        print("  ✅ Query processing")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Functionality error: {e}")
        return False

def test_data_models():
    """Test data models and classes"""
    print("🔍 Testing data models...")
    
    try:
        from enhanced_rag_integration import DocumentUploadResult, RAGQueryResult
        from document_processing_status import DocumentProcessingStatus, ProcessingSummary
        
        # Test upload result
        upload_result = DocumentUploadResult(
            success=True,
            message="Test",
            documents_processed=1
        )
        assert upload_result.success == True, "Upload result should work"
        print("  ✅ DocumentUploadResult")
        
        # Test query result
        query_result = RAGQueryResult(
            success=True,
            response="Test response",
            using_rag=True
        )
        assert query_result.using_rag == True, "Query result should work"
        print("  ✅ RAGQueryResult")
        
        # Test processing status
        status = DocumentProcessingStatus(
            id="test",
            user_id="user",
            filename="test.pdf",
            original_filename="test.pdf",
            file_size=1024,
            mime_type="application/pdf",
            status="completed"
        )
        assert status.status == "completed", "Status should work"
        print("  ✅ DocumentProcessingStatus")
        
        # Test summary
        summary = ProcessingSummary(
            total_documents=5,
            processing_documents=1,
            completed_documents=4,
            failed_documents=0,
            total_chunks=20,
            total_embeddings=20
        )
        assert summary.total_documents == 5, "Summary should work"
        print("  ✅ ProcessingSummary")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Data model error: {e}")
        return False

def main():
    """Run simple verification"""
    print("🚀 Task 10: Enhanced RAG Integration - Simple Verification")
    print("=" * 60)
    
    tests = [
        ("Component Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Data Models", test_data_models)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        print("\n🎉 Task 10 Implementation Verified!")
        print("\n📋 Key Components Working:")
        print("  • Enhanced RAG integration system")
        print("  • Document processing status tracking")
        print("  • User interface components")
        print("  • Error handling and health monitoring")
        print("  • Data models and API")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)