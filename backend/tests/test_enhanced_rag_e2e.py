"""
End-to-End Tests for Enhanced RAG System
Tests the complete workflow from document upload to search
"""

import asyncio
import pytest
import tempfile
import os
from uuid import uuid4
from typing import Dict, Any

from app.core.database import get_db
from app.services.enhanced_rag import EnhancedRAGService
from app.services.embeddings import embeddings_service
from app.models.document import DocumentUploadResponse, DocumentChunk


class TestEnhancedRAGE2E:
    """End-to-end tests for enhanced RAG system"""
    
    @pytest.fixture
    def rag_service(self):
        """Create RAG service instance"""
        db = get_db()
        return EnhancedRAGService(db)
    
    @pytest.fixture
    def test_user_id(self):
        """Generate test user ID"""
        return uuid4()
    
    @pytest.fixture
    def test_conversation_id(self):
        """Generate test conversation ID"""
        return uuid4()
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create sample PDF content for testing"""
        # This would normally be actual PDF bytes
        # For testing, we'll use a simple text representation
        return b"Sample PDF content for pharmaceutical research on drug interactions"
    
    @pytest.fixture
    def sample_text_content(self):
        """Create sample text content for testing"""
        return b"""
        Pharmaceutical Research Document
        
        This document contains information about drug interactions and mechanisms of action.
        
        Chapter 1: Introduction
        Pharmacology is the study of drug action and interaction with biological systems.
        
        Chapter 2: Drug Interactions
        Drug interactions can occur when two or more drugs are taken together.
        These interactions can be pharmacokinetic or pharmacodynamic in nature.
        
        Chapter 3: Mechanisms of Action
        Understanding how drugs work at the molecular level is crucial for safe prescribing.
        """
    
    @pytest.mark.asyncio
    async def test_complete_document_workflow(
        self, 
        rag_service: EnhancedRAGService,
        test_user_id,
        test_conversation_id,
        sample_text_content
    ):
        """Test complete document processing workflow"""
        
        # Test document upload and processing
        filename = "test_document.txt"
        
        upload_response = await rag_service.process_uploaded_file(
            file_content=sample_text_content,
            filename=filename,
            conversation_id=test_conversation_id,
            user_id=test_user_id
        )
        
        # Verify upload response
        assert isinstance(upload_response, DocumentUploadResponse)
        assert upload_response.success is True
        assert upload_response.chunk_count > 0
        assert upload_response.processing_time is not None
        assert upload_response.processing_time > 0
        
        print(f"✅ Document processed: {upload_response.chunk_count} chunks in {upload_response.processing_time:.2f}s")
        
        # Test similarity search
        search_query = "drug interactions"
        
        search_results = await rag_service.search_similar_chunks(
            query=search_query,
            conversation_id=test_conversation_id,
            user_id=test_user_id,
            max_results=5,
            similarity_threshold=0.1  # Lower threshold for testing
        )
        
        # Verify search results
        assert isinstance(search_results, list)
        assert len(search_results) > 0
        
        for chunk in search_results:
            assert isinstance(chunk, DocumentChunk)
            assert chunk.id is not None
            assert chunk.conversation_id == test_conversation_id
            assert chunk.content is not None
            assert len(chunk.content) > 0
            assert chunk.similarity is not None
        
        print(f"✅ Search completed: {len(search_results)} results found")
        
        # Test context generation
        context = await rag_service.get_conversation_context(
            query=search_query,
            conversation_id=test_conversation_id,
            user_id=test_user_id,
            max_chunks=10
        )
        
        # Verify context
        assert isinstance(context, str)
        assert len(context) > 0
        assert "drug" in context.lower() or "pharmaceutical" in context.lower()
        
        print(f"✅ Context generated: {len(context)} characters")
        
        # Test getting all conversation chunks
        all_chunks = await rag_service.get_all_conversation_chunks(
            conversation_id=test_conversation_id,
            user_id=test_user_id
        )
        
        # Verify all chunks retrieval
        assert isinstance(all_chunks, list)
        assert len(all_chunks) == upload_response.chunk_count
        
        print(f"✅ All chunks retrieved: {len(all_chunks)} chunks")
        
        return {
            "upload_response": upload_response,
            "search_results": search_results,
            "context": context,
            "all_chunks": all_chunks
        }
    
    @pytest.mark.asyncio
    async def test_multiple_document_workflow(
        self,
        rag_service: EnhancedRAGService,
        test_user_id,
        test_conversation_id
    ):
        """Test workflow with multiple documents"""
        
        documents = [
            {
                "filename": "doc1.txt",
                "content": b"Document 1: Information about aspirin and its anti-inflammatory properties."
            },
            {
                "filename": "doc2.txt", 
                "content": b"Document 2: Research on ibuprofen and pain management mechanisms."
            },
            {
                "filename": "doc3.txt",
                "content": b"Document 3: Study of drug-drug interactions between NSAIDs and anticoagulants."
            }
        ]
        
        upload_results = []
        
        # Upload all documents
        for doc in documents:
            result = await rag_service.process_uploaded_file(
                file_content=doc["content"],
                filename=doc["filename"],
                conversation_id=test_conversation_id,
                user_id=test_user_id
            )
            
            assert result.success is True
            assert result.chunk_count > 0
            upload_results.append(result)
        
        total_chunks = sum(result.chunk_count for result in upload_results)
        print(f"✅ Multiple documents processed: {len(documents)} docs, {total_chunks} total chunks")
        
        # Test search across all documents
        search_queries = [
            "aspirin anti-inflammatory",
            "ibuprofen pain management", 
            "drug interactions NSAIDs"
        ]
        
        for query in search_queries:
            results = await rag_service.search_similar_chunks(
                query=query,
                conversation_id=test_conversation_id,
                user_id=test_user_id,
                max_results=10,
                similarity_threshold=0.1
            )
            
            assert len(results) > 0
            print(f"✅ Search '{query}': {len(results)} results")
        
        # Test context generation with multiple documents
        context = await rag_service.get_conversation_context(
            query="drug interactions and pain management",
            conversation_id=test_conversation_id,
            user_id=test_user_id,
            max_chunks=20
        )
        
        assert len(context) > 0
        # Should contain content from multiple documents
        assert "aspirin" in context.lower() or "ibuprofen" in context.lower()
        
        print(f"✅ Multi-document context: {len(context)} characters")
        
        return {
            "upload_results": upload_results,
            "total_chunks": total_chunks,
            "context": context
        }
    
    @pytest.mark.asyncio
    async def test_embedding_quality(
        self,
        rag_service: EnhancedRAGService,
        test_user_id,
        test_conversation_id
    ):
        """Test embedding quality and similarity"""
        
        # Upload document with known content
        test_content = b"""
        Pharmacokinetics and Pharmacodynamics
        
        Pharmacokinetics describes what the body does to a drug, including absorption,
        distribution, metabolism, and excretion (ADME).
        
        Pharmacodynamics describes what the drug does to the body, including
        mechanism of action, dose-response relationships, and therapeutic effects.
        """
        
        upload_result = await rag_service.process_uploaded_file(
            file_content=test_content,
            filename="pharmacology.txt",
            conversation_id=test_conversation_id,
            user_id=test_user_id
        )
        
        assert upload_result.success is True
        
        # Test related queries with expected similarity
        test_cases = [
            {
                "query": "pharmacokinetics ADME",
                "expected_min_similarity": 0.3,
                "should_find_content": "absorption"
            },
            {
                "query": "pharmacodynamics mechanism",
                "expected_min_similarity": 0.3,
                "should_find_content": "dose-response"
            },
            {
                "query": "drug metabolism excretion",
                "expected_min_similarity": 0.2,
                "should_find_content": "pharmacokinetics"
            }
        ]
        
        for test_case in test_cases:
            results = await rag_service.search_similar_chunks(
                query=test_case["query"],
                conversation_id=test_conversation_id,
                user_id=test_user_id,
                max_results=5,
                similarity_threshold=0.1
            )
            
            assert len(results) > 0, f"No results for query: {test_case['query']}"
            
            # Check similarity scores
            max_similarity = max(chunk.similarity for chunk in results)
            assert max_similarity >= test_case["expected_min_similarity"], \
                f"Low similarity for '{test_case['query']}': {max_similarity}"
            
            # Check content relevance
            all_content = " ".join(chunk.content for chunk in results).lower()
            assert test_case["should_find_content"].lower() in all_content, \
                f"Expected content '{test_case['should_find_content']}' not found"
            
            print(f"✅ Query '{test_case['query']}': max similarity {max_similarity:.3f}")
        
        return True
    
    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        rag_service: EnhancedRAGService,
        test_user_id,
        test_conversation_id
    ):
        """Test error handling scenarios"""
        
        # Test empty file
        empty_result = await rag_service.process_uploaded_file(
            file_content=b"",
            filename="empty.txt",
            conversation_id=test_conversation_id,
            user_id=test_user_id
        )
        
        assert empty_result.success is False
        assert "empty" in empty_result.message.lower()
        
        # Test unsupported file type
        unsupported_result = await rag_service.process_uploaded_file(
            file_content=b"some content",
            filename="test.xyz",
            conversation_id=test_conversation_id,
            user_id=test_user_id
        )
        
        assert unsupported_result.success is False
        assert "unsupported" in unsupported_result.message.lower()
        
        # Test search with no documents
        empty_conversation_id = uuid4()
        empty_results = await rag_service.search_similar_chunks(
            query="test query",
            conversation_id=empty_conversation_id,
            user_id=test_user_id,
            max_results=5
        )
        
        assert isinstance(empty_results, list)
        assert len(empty_results) == 0
        
        print("✅ Error handling tests passed")
        
        return True
    
    @pytest.mark.asyncio
    async def test_service_health(self, rag_service: EnhancedRAGService):
        """Test service health check"""
        
        health = await rag_service.get_service_health()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in health
        
        # Check component health
        components = health["components"]
        assert "embeddings" in components
        assert "document_loader" in components
        assert "text_splitter" in components
        assert "database" in components
        
        print(f"✅ Service health: {health['status']}")
        
        return health
    
    @pytest.mark.asyncio
    async def test_performance_metrics(self, rag_service: EnhancedRAGService):
        """Test performance tracking"""
        
        stats = rag_service.get_processing_stats()
        
        assert isinstance(stats, dict)
        assert "service_type" in stats
        assert stats["service_type"] == "EnhancedRAGService"
        assert "langchain_integration" in stats
        assert stats["langchain_integration"] is True
        assert "supported_formats" in stats
        assert "features" in stats
        
        print(f"✅ Performance stats retrieved: {len(stats['features'])} features")
        
        return stats


# Integration test runner
async def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting Enhanced RAG E2E Integration Tests")
    print("=" * 60)
    
    test_instance = TestEnhancedRAGE2E()
    
    # Create test fixtures
    db = get_db()
    rag_service = EnhancedRAGService(db)
    test_user_id = uuid4()
    test_conversation_id = uuid4()
    
    sample_text = b"""
    Pharmaceutical Research Document
    
    This document contains information about drug interactions and mechanisms of action.
    
    Chapter 1: Introduction
    Pharmacology is the study of drug action and interaction with biological systems.
    
    Chapter 2: Drug Interactions
    Drug interactions can occur when two or more drugs are taken together.
    These interactions can be pharmacokinetic or pharmacodynamic in nature.
    """
    
    try:
        # Test 1: Complete workflow
        print("\n📋 Test 1: Complete Document Workflow")
        result1 = await test_instance.test_complete_document_workflow(
            rag_service, test_user_id, test_conversation_id, sample_text
        )
        
        # Test 2: Multiple documents
        print("\n📋 Test 2: Multiple Document Workflow")
        test_conversation_id2 = uuid4()
        result2 = await test_instance.test_multiple_document_workflow(
            rag_service, test_user_id, test_conversation_id2
        )
        
        # Test 3: Embedding quality
        print("\n📋 Test 3: Embedding Quality")
        test_conversation_id3 = uuid4()
        result3 = await test_instance.test_embedding_quality(
            rag_service, test_user_id, test_conversation_id3
        )
        
        # Test 4: Error handling
        print("\n📋 Test 4: Error Handling")
        test_conversation_id4 = uuid4()
        result4 = await test_instance.test_error_handling(
            rag_service, test_user_id, test_conversation_id4
        )
        
        # Test 5: Service health
        print("\n📋 Test 5: Service Health")
        result5 = await test_instance.test_service_health(rag_service)
        
        # Test 6: Performance metrics
        print("\n📋 Test 6: Performance Metrics")
        result6 = await test_instance.test_performance_metrics(rag_service)
        
        print("\n" + "=" * 60)
        print("🎉 All integration tests PASSED!")
        
        return {
            "success": True,
            "results": {
                "complete_workflow": result1,
                "multiple_documents": result2,
                "embedding_quality": result3,
                "error_handling": result4,
                "service_health": result5,
                "performance_metrics": result6
            }
        }
        
    except Exception as e:
        print(f"\n💥 Integration test FAILED: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Run integration tests directly
    result = asyncio.run(run_integration_tests())
    
    if result["success"]:
        print("\n✅ Integration tests completed successfully")
        exit(0)
    else:
        print(f"\n❌ Integration tests failed: {result['error']}")
        exit(1)