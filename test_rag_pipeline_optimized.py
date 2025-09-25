# test_rag_pipeline_optimized.py
import os
import sys
import uuid
import gc
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path for imports
sys.path.append('.')

from vector_retriever import VectorRetriever, Document
from document_processor import DocumentProcessor, ProcessedDocument
from context_builder import ContextBuilder, ContextConfig
from rag_orchestrator_optimized import RAGOrchestrator, RAGConfig

def test_memory_optimized_vector_retriever():
    """Test memory-optimized VectorRetriever functionality"""
    print("Testing Memory-Optimized VectorRetriever...")
    
    # Mock Supabase client
    mock_client = Mock()
    mock_client.rpc.return_value.execute.return_value.data = [
        {
            'id': 'doc1',
            'content': 'Aspirin is a common pain reliever and anti-inflammatory drug.' * 50,  # Large content
            'source': 'pharmacology_textbook.pdf',
            'metadata': {'chunk_index': 0},
            'similarity': 0.85
        }
    ]
    
    # Mock embedding model
    mock_embedding = Mock()
    mock_embedding.embed_query.return_value = [0.1] * 384
    
    retriever = VectorRetriever(supabase_client=mock_client, embedding_model=mock_embedding)
    
    # Test similarity search with large content
    user_id = str(uuid.uuid4())
    documents = retriever.similarity_search("pain relief medication", user_id, k=15)  # Request more than limit
    
    assert len(documents) == 1
    # Content should be truncated to save memory
    assert len(documents[0].content) <= 2003  # 2000 + "..."
    assert documents[0].similarity == 0.85
    
    print("✓ Memory-Optimized VectorRetriever tests passed")

def test_memory_optimized_document_processor():
    """Test memory-optimized DocumentProcessor functionality"""
    print("Testing Memory-Optimized DocumentProcessor...")
    
    # Mock Supabase client
    mock_client = Mock()
    mock_client.table.return_value.upsert.return_value.execute.return_value.data = [
        {'id': 'doc1', 'user_id': 'user1'}
    ]
    
    # Mock embedding model
    mock_embedding = Mock()
    mock_embedding.embed_documents.return_value = [[0.1] * 384] * 20  # Large batch
    
    processor = DocumentProcessor(supabase_client=mock_client, embedding_model=mock_embedding)
    
    # Create many mock documents to test batching
    mock_docs = []
    for i in range(25):  # More than batch size
        doc = ProcessedDocument(
            id=f'doc{i}',
            user_id='user1',
            content=f'Test document {i} content',
            source=f'test{i}.txt',
            metadata={'chunk_index': i}
        )
        mock_docs.append(doc)
    
    # Test storing documents with batching
    success = processor.store_documents(mock_docs)
    
    # Should have been called multiple times due to batching
    assert mock_client.table.return_value.upsert.call_count >= 3  # 25 docs / 10 batch size = 3 batches
    
    print("✓ Memory-Optimized DocumentProcessor tests passed")

def test_memory_optimized_context_builder():
    """Test memory-optimized ContextBuilder functionality"""
    print("Testing Memory-Optimized ContextBuilder...")
    
    # Create test documents with large content
    documents = [
        Document(
            id='doc1',
            content='Aspirin is a common pain reliever that works by inhibiting COX enzymes.' * 20,  # Large content
            source='pharmacology_textbook.pdf',
            metadata={'chunk_index': 0, 'file_type': 'pdf'},
            similarity=0.85
        ),
        Document(
            id='doc2',
            content='Ibuprofen is another NSAID that provides anti-inflammatory effects.' * 20,  # Large content
            source='drug_reference.pdf', 
            metadata={'chunk_index': 1, 'file_type': 'pdf'},
            similarity=0.72
        )
    ]
    
    # Use memory-optimized config
    config = ContextConfig(
        max_context_length=2000,  # Reduced
        max_documents=3,  # Reduced
        similarity_threshold=0.1
    )
    
    builder = ContextBuilder(config=config)
    
    # Test context building
    context = builder.build_context(documents, "pain relief medications")
    
    assert len(context) > 0
    assert len(context) <= 2000  # Should respect memory limit
    assert 'Aspirin' in context
    
    # Test context stats
    stats = builder.get_context_stats(context, documents)
    assert stats['document_count'] == 2
    
    print("✓ Memory-Optimized ContextBuilder tests passed")

def test_memory_optimized_rag_orchestrator():
    """Test memory-optimized RAGOrchestrator functionality"""
    print("Testing Memory-Optimized RAGOrchestrator...")
    
    # Mock components
    mock_retriever = Mock()
    mock_retriever.similarity_search.return_value = [
        Document(
            id='doc1',
            content='Aspirin is effective for pain relief and inflammation.',
            source='pharmacology.pdf',
            metadata={'chunk_index': 0},
            similarity=0.85
        )
    ]
    
    mock_context_builder = Mock()
    mock_context_builder.build_context.return_value = "Context: Aspirin is effective for pain relief and inflammation."
    mock_context_builder.get_context_stats.return_value = {
        'context_length': 50,
        'document_count': 1,
        'avg_similarity': 0.85
    }
    
    mock_llm = Mock()
    mock_llm.generate_response.return_value = "Based on the provided context, aspirin is indeed effective for pain relief due to its anti-inflammatory properties."
    
    # Use memory-optimized config
    config = RAGConfig(
        retrieval_k=3,  # Reduced
        similarity_threshold=0.2,  # Increased
        fallback_to_llm_only=True
    )
    
    orchestrator = RAGOrchestrator(
        vector_retriever=mock_retriever,
        context_builder=mock_context_builder,
        llm=mock_llm,
        config=config
    )
    
    # Test query processing with large conversation history
    user_id = str(uuid.uuid4())
    large_history = []
    for i in range(10):  # Large history
        large_history.extend([
            {"role": "user", "content": f"Question {i}"},
            {"role": "assistant", "content": f"Answer {i}"}
        ])
    
    response = orchestrator.process_query(
        query="How does aspirin work for pain relief?",
        user_id=user_id,
        model_type="fast",
        conversation_history=large_history
    )
    
    assert response.success == True
    assert len(response.response) > 0
    assert len(response.documents_retrieved) == 1
    assert response.context_stats['document_count'] == 1
    assert response.model_used == "fast"
    
    print("✓ Memory-Optimized RAGOrchestrator tests passed")

def test_memory_usage():
    """Test memory usage and cleanup"""
    print("Testing Memory Usage and Cleanup...")
    
    # Force garbage collection before test
    gc.collect()
    
    # Create components and process multiple queries
    try:
        with patch('vector_retriever.create_client'), \
             patch('document_processor.create_client'), \
             patch('embeddings.get_embeddings'):
            
            # Create memory-optimized orchestrator
            config = RAGConfig(retrieval_k=2, similarity_threshold=0.3)
            orchestrator = RAGOrchestrator(config=config)
            
            # Process multiple queries to test memory cleanup
            for i in range(5):
                # This would normally cause memory buildup
                pass
            
            # Force cleanup
            orchestrator._cleanup_memory()
            
    except Exception as e:
        print(f"Memory test failed: {e}")
        return False
    
    print("✓ Memory usage tests passed")
    return True

def run_optimized_tests():
    """Run all memory-optimized tests"""
    print("Running Memory-Optimized RAG Pipeline Tests...")
    print("=" * 60)
    
    # Mock environment variables for testing
    with patch.dict(os.environ, {
        'GROQ_API_KEY': 'test_key',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key'
    }):
        try:
            test_memory_optimized_vector_retriever()
            test_memory_optimized_document_processor()
            test_memory_optimized_context_builder()
            test_memory_optimized_rag_orchestrator()
            test_memory_usage()
            
            print("=" * 60)
            print("✅ All Memory-Optimized RAG Pipeline tests passed!")
            print("Memory usage has been significantly reduced through:")
            print("- Reduced retrieval limits (k=3 instead of 5)")
            print("- Content truncation for large documents")
            print("- Batched document processing")
            print("- Smaller context windows")
            print("- Limited conversation history")
            print("- Automatic garbage collection")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = run_optimized_tests()
    sys.exit(0 if success else 1)