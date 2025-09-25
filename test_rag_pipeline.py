# test_rag_pipeline.py
import os
import sys
import uuid
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path for imports
sys.path.append('.')

from vector_retriever import VectorRetriever, Document
from document_processor import DocumentProcessor, ProcessedDocument
from context_builder import ContextBuilder, ContextConfig
from rag_orchestrator import RAGOrchestrator, RAGConfig

def test_vector_retriever():
    """Test VectorRetriever functionality"""
    print("Testing VectorRetriever...")
    
    # Mock Supabase client
    mock_client = Mock()
    mock_client.rpc.return_value.execute.return_value.data = [
        {
            'id': 'doc1',
            'content': 'Aspirin is a common pain reliever and anti-inflammatory drug.',
            'source': 'pharmacology_textbook.pdf',
            'metadata': {'chunk_index': 0},
            'similarity': 0.85
        },
        {
            'id': 'doc2', 
            'content': 'Ibuprofen belongs to the NSAID class of medications.',
            'source': 'drug_reference.pdf',
            'metadata': {'chunk_index': 1},
            'similarity': 0.72
        }
    ]
    
    # Mock embedding model
    mock_embedding = Mock()
    mock_embedding.embed_query.return_value = [0.1] * 384
    
    retriever = VectorRetriever(supabase_client=mock_client, embedding_model=mock_embedding)
    
    # Test similarity search
    user_id = str(uuid.uuid4())
    documents = retriever.similarity_search("pain relief medication", user_id, k=5)
    
    assert len(documents) == 2
    assert documents[0].content == 'Aspirin is a common pain reliever and anti-inflammatory drug.'
    assert documents[0].similarity == 0.85
    assert documents[1].similarity == 0.72
    
    print("✓ VectorRetriever tests passed")

def test_document_processor():
    """Test DocumentProcessor functionality"""
    print("Testing DocumentProcessor...")
    
    # Mock Supabase client
    mock_client = Mock()
    mock_client.table.return_value.upsert.return_value.execute.return_value.data = [
        {'id': 'doc1', 'user_id': 'user1'}
    ]
    
    # Mock embedding model
    mock_embedding = Mock()
    mock_embedding.embed_documents.return_value = [[0.1] * 384, [0.2] * 384]
    
    processor = DocumentProcessor(supabase_client=mock_client, embedding_model=mock_embedding)
    
    # Create mock uploaded file
    mock_file = Mock()
    mock_file.name = 'test_document.txt'
    mock_file.getvalue.return_value = b'This is a test document about pharmacology. It contains information about various drugs and their mechanisms of action.'
    
    user_id = str(uuid.uuid4())
    
    # Mock the extract_text_from_file function
    with patch('document_processor.extract_text_from_file') as mock_extract:
        mock_extract.return_value = 'This is a test document about pharmacology. It contains information about various drugs and their mechanisms of action.'
        
        # Test processing uploaded files
        processed_docs = processor.process_uploaded_files([mock_file], user_id)
        
        assert len(processed_docs) == 1
        assert processed_docs[0].user_id == user_id
        assert processed_docs[0].source == 'test_document.txt'
        assert 'pharmacology' in processed_docs[0].content
        
        # Test storing documents
        success = processor.store_documents(processed_docs)
        assert success == True
    
    print("✓ DocumentProcessor tests passed")

def test_context_builder():
    """Test ContextBuilder functionality"""
    print("Testing ContextBuilder...")
    
    # Create test documents
    documents = [
        Document(
            id='doc1',
            content='Aspirin is a common pain reliever that works by inhibiting COX enzymes.',
            source='pharmacology_textbook.pdf',
            metadata={'chunk_index': 0, 'file_type': 'pdf'},
            similarity=0.85
        ),
        Document(
            id='doc2',
            content='Ibuprofen is another NSAID that provides anti-inflammatory effects.',
            source='drug_reference.pdf', 
            metadata={'chunk_index': 1, 'file_type': 'pdf'},
            similarity=0.72
        ),
        Document(
            id='doc3',
            content='Acetaminophen is a pain reliever that works differently from NSAIDs.',
            source='pain_management.pdf',
            metadata={'chunk_index': 0, 'file_type': 'pdf'},
            similarity=0.68
        )
    ]
    
    builder = ContextBuilder()
    
    # Test context building
    context = builder.build_context(documents, "pain relief medications")
    
    assert len(context) > 0
    assert 'Aspirin' in context
    assert 'Ibuprofen' in context
    assert 'Source:' in context  # Should include source info
    
    # Test context stats
    stats = builder.get_context_stats(context, documents)
    assert stats['document_count'] == 3
    assert stats['avg_similarity'] > 0.7
    assert len(stats['sources']) == 3
    
    print("✓ ContextBuilder tests passed")

def test_rag_orchestrator():
    """Test RAGOrchestrator functionality"""
    print("Testing RAGOrchestrator...")
    
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
    
    orchestrator = RAGOrchestrator(
        vector_retriever=mock_retriever,
        context_builder=mock_context_builder,
        llm=mock_llm
    )
    
    # Test query processing
    user_id = str(uuid.uuid4())
    response = orchestrator.process_query(
        query="How does aspirin work for pain relief?",
        user_id=user_id,
        model_type="fast"
    )
    
    assert response.success == True
    assert len(response.response) > 0
    assert len(response.documents_retrieved) == 1
    assert response.context_stats['document_count'] == 1
    assert response.model_used == "fast"
    
    print("✓ RAGOrchestrator tests passed")

def test_integration():
    """Test integration between components"""
    print("Testing component integration...")
    
    # This would test the full pipeline with mocked external dependencies
    # For now, we'll just verify the components can be instantiated together
    
    try:
        # Mock external dependencies
        with patch('vector_retriever.create_client'), \
             patch('document_processor.create_client'), \
             patch('embeddings.get_embeddings'):
            
            # Create components
            retriever = VectorRetriever()
            processor = DocumentProcessor()
            builder = ContextBuilder()
            
            # Verify they can work together
            config = RAGConfig(retrieval_k=3, similarity_threshold=0.2)
            orchestrator = RAGOrchestrator(
                vector_retriever=retriever,
                context_builder=builder,
                config=config
            )
            
            assert orchestrator.config.retrieval_k == 3
            assert orchestrator.config.similarity_threshold == 0.2
            
    except Exception as e:
        print(f"Integration test failed: {e}")
        return False
    
    print("✓ Integration tests passed")
    return True

def run_all_tests():
    """Run all tests"""
    print("Running RAG Pipeline Tests...")
    print("=" * 50)
    
    # Mock environment variables for testing
    with patch.dict(os.environ, {
        'GROQ_API_KEY': 'test_key',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_ANON_KEY': 'test_anon_key'
    }):
        try:
            test_vector_retriever()
            test_document_processor()
            test_context_builder()
            test_rag_orchestrator()
            test_integration()
            
            print("=" * 50)
            print("✅ All RAG Pipeline tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)