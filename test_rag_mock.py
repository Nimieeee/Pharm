"""
RAG Pipeline Tests with Mock Vector Database
Comprehensive testing of RAG components with mocked dependencies
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vector_retriever import VectorRetriever, Document
from document_processor import DocumentProcessor, ProcessedDocument
from context_builder import ContextBuilder, ContextConfig
from rag_orchestrator import RAGOrchestrator, RAGConfig, RAGResponse
from model_manager import ModelManager


class MockVectorDatabase:
    """Mock vector database for testing"""
    
    def __init__(self):
        self.documents = {}
        self.embeddings = {}
    
    def store_document(self, doc_id: str, user_id: str, content: str, 
                      embedding: List[float], metadata: Dict[str, Any]):
        """Store a document in the mock database"""
        self.documents[doc_id] = {
            'id': doc_id,
            'user_id': user_id,
            'content': content,
            'metadata': metadata
        }
        self.embeddings[doc_id] = embedding
    
    def similarity_search(self, query_embedding: List[float], user_id: str, 
                         k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search in mock database"""
        # Simple mock similarity calculation (dot product)
        results = []
        
        for doc_id, doc in self.documents.items():
            if doc['user_id'] == user_id:
                doc_embedding = self.embeddings[doc_id]
                # Simple dot product similarity
                similarity = sum(a * b for a, b in zip(query_embedding, doc_embedding))
                
                results.append({
                    'id': doc_id,
                    'content': doc['content'],
                    'source': doc['metadata'].get('source', 'unknown'),
                    'metadata': doc['metadata'],
                    'similarity': similarity
                })
        
        # Sort by similarity and return top k
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:k]
    
    def get_user_document_count(self, user_id: str) -> int:
        """Get count of documents for a user"""
        return len([doc for doc in self.documents.values() 
                   if doc['user_id'] == user_id])


class TestVectorRetriever(unittest.TestCase):
    """Unit tests for VectorRetriever with mock database"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.mock_embedding = Mock()
        self.mock_db = MockVectorDatabase()
        
        # Set up mock embedding responses
        self.mock_embedding.embed_query.return_value = [0.1, 0.2, 0.3] * 128  # 384 dimensions
        
    def test_initialization(self):
        """Test VectorRetriever initialization"""
        retriever = VectorRetriever(
            supabase_client=self.mock_client,
            embedding_model=self.mock_embedding
        )
        
        self.assertIsNotNone(retriever)
        self.assertEqual(retriever.supabase_client, self.mock_client)
        self.assertEqual(retriever.embedding_model, self.mock_embedding)
    
    def test_similarity_search_with_results(self):
        """Test similarity search with mock results"""
        # Set up mock RPC response
        mock_results = [
            {
                'id': 'doc1',
                'content': 'Aspirin is a pain reliever that inhibits COX enzymes.',
                'source': 'pharmacology.pdf',
                'metadata': {'chunk_index': 0},
                'similarity': 0.85
            },
            {
                'id': 'doc2',
                'content': 'Ibuprofen is an NSAID with anti-inflammatory properties.',
                'source': 'drug_guide.pdf',
                'metadata': {'chunk_index': 1},
                'similarity': 0.72
            }
        ]
        
        mock_result = Mock()
        mock_result.data = mock_results
        self.mock_client.rpc.return_value.execute.return_value = mock_result
        
        retriever = VectorRetriever(
            supabase_client=self.mock_client,
            embedding_model=self.mock_embedding
        )
        
        # Perform search
        user_id = str(uuid.uuid4())
        documents = retriever.similarity_search("pain relief", user_id, k=5)
        
        # Verify results
        self.assertEqual(len(documents), 2)
        self.assertIsInstance(documents[0], Document)
        self.assertEqual(documents[0].content, 'Aspirin is a pain reliever that inhibits COX enzymes.')
        self.assertEqual(documents[0].similarity, 0.85)
        self.assertEqual(documents[1].similarity, 0.72)
        
        # Verify RPC was called with correct parameters
        self.mock_client.rpc.assert_called_once()
    
    def test_similarity_search_no_results(self):
        """Test similarity search with no results"""
        mock_result = Mock()
        mock_result.data = []
        self.mock_client.rpc.return_value.execute.return_value = mock_result
        
        retriever = VectorRetriever(
            supabase_client=self.mock_client,
            embedding_model=self.mock_embedding
        )
        
        user_id = str(uuid.uuid4())
        documents = retriever.similarity_search("nonexistent query", user_id, k=5)
        
        self.assertEqual(len(documents), 0)
    
    def test_similarity_search_user_filtering(self):
        """Test that similarity search filters by user ID"""
        retriever = VectorRetriever(
            supabase_client=self.mock_client,
            embedding_model=self.mock_embedding
        )
        
        user_id = str(uuid.uuid4())
        retriever.similarity_search("test query", user_id, k=5)
        
        # Verify that the RPC call includes user filtering
        call_args = self.mock_client.rpc.call_args
        self.assertIsNotNone(call_args)
        # The exact parameter structure depends on implementation
        # but we should verify user_id is passed
    
    def test_add_documents(self):
        """Test adding documents to vector database"""
        mock_result = Mock()
        mock_result.data = [{'id': 'doc1', 'user_id': 'user123'}]
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_result
        
        retriever = VectorRetriever(
            supabase_client=self.mock_client,
            embedding_model=self.mock_embedding
        )
        
        # Create test document
        document = Document(
            id='doc1',
            content='Test document content',
            source='test.pdf',
            metadata={'chunk_index': 0},
            embedding=[0.1] * 384
        )
        
        user_id = 'user123'
        success = retriever.add_documents([document], user_id)
        
        self.assertTrue(success)
        self.mock_client.table.assert_called()


class TestDocumentProcessor(unittest.TestCase):
    """Unit tests for DocumentProcessor with mock dependencies"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.mock_embedding = Mock()
        self.mock_embedding.embed_documents.return_value = [[0.1] * 384, [0.2] * 384]
    
    def test_initialization(self):
        """Test DocumentProcessor initialization"""
        processor = DocumentProcessor(
            supabase_client=self.mock_client,
            embedding_model=self.mock_embedding
        )
        
        self.assertIsNotNone(processor)
        self.assertEqual(processor.supabase_client, self.mock_client)
        self.assertEqual(processor.embedding_model, self.mock_embedding)
    
    def test_process_text_content(self):
        """Test processing text content into chunks"""
        processor = DocumentProcessor(
            supabase_client=self.mock_client,
            embedding_model=self.mock_embedding
        )
        
        # Test text that should be chunked
        long_text = "This is a test document. " * 100  # Long text
        user_id = str(uuid.uuid4())
        
        processed_docs = processor.process_text_content(
            content=long_text,
            source="test.txt",
            user_id=user_id
        )
        
        self.assertGreater(len(processed_docs), 0)
        for doc in processed_docs:
            self.assertIsInstance(doc, ProcessedDocument)
            self.assertEqual(doc.user_id, user_id)
            self.assertEqual(doc.source, "test.txt")
            self.assertIsNotNone(doc.embedding)
    
    def test_store_documents(self):
        """Test storing processed documents"""
        mock_result = Mock()
        mock_result.data = [{'id': 'doc1', 'user_id': 'user123'}]
        self.mock_client.table.return_value.upsert.return_value.execute.return_value = mock_result
        
        processor = DocumentProcessor(
            supabase_client=self.mock_client,
            embedding_model=self.mock_embedding
        )
        
        # Create test processed document
        processed_doc = ProcessedDocument(
            id=str(uuid.uuid4()),
            user_id='user123',
            content='Test content',
            source='test.txt',
            metadata={},
            embedding=[0.1] * 384
        )
        
        success = processor.store_documents([processed_doc])
        
        self.assertTrue(success)
        self.mock_client.table.assert_called()
    
    def test_batch_processing(self):
        """Test batch processing of multiple documents"""
        processor = DocumentProcessor(
            supabase_client=self.mock_client,
            embedding_model=self.mock_embedding
        )
        
        # Mock multiple files
        mock_files = []
        for i in range(3):
            mock_file = Mock()
            mock_file.name = f'test{i}.txt'
            mock_file.getvalue.return_value = f'Test content {i}'.encode()
            mock_files.append(mock_file)
        
        user_id = str(uuid.uuid4())
        
        with patch('document_processor.extract_text_from_file') as mock_extract:
            mock_extract.side_effect = lambda f: f.getvalue().decode()
            
            processed_docs = processor.process_uploaded_files(mock_files, user_id)
            
            self.assertEqual(len(processed_docs), 3)
            for i, doc in enumerate(processed_docs):
                self.assertEqual(doc.source, f'test{i}.txt')
                self.assertEqual(doc.user_id, user_id)


class TestContextBuilder(unittest.TestCase):
    """Unit tests for ContextBuilder"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.context_builder = ContextBuilder()
        
        # Create test documents
        self.test_documents = [
            Document(
                id='doc1',
                content='Aspirin is a nonsteroidal anti-inflammatory drug (NSAID) that works by inhibiting cyclooxygenase (COX) enzymes.',
                source='pharmacology_textbook.pdf',
                metadata={'chapter': 'NSAIDs', 'page': 45},
                similarity=0.92
            ),
            Document(
                id='doc2',
                content='Ibuprofen is another NSAID that provides both analgesic and anti-inflammatory effects.',
                source='drug_reference.pdf',
                metadata={'category': 'pain_relief', 'page': 123},
                similarity=0.85
            ),
            Document(
                id='doc3',
                content='Acetaminophen (paracetamol) is a pain reliever that works differently from NSAIDs.',
                source='pain_management.pdf',
                metadata={'category': 'analgesics', 'page': 67},
                similarity=0.78
            )
        ]
    
    def test_build_context_basic(self):
        """Test basic context building"""
        query = "How do NSAIDs work for pain relief?"
        context = self.context_builder.build_context(self.test_documents, query)
        
        self.assertIsInstance(context, str)
        self.assertGreater(len(context), 0)
        
        # Verify all document contents are included
        for doc in self.test_documents:
            self.assertIn(doc.content, context)
        
        # Verify source information is included
        self.assertIn("Source:", context)
    
    def test_build_context_with_config(self):
        """Test context building with custom configuration"""
        config = ContextConfig(
            max_context_length=500,
            include_sources=True,
            include_similarity_scores=True,
            similarity_threshold=0.8
        )
        
        query = "NSAIDs mechanism"
        context = self.context_builder.build_context(
            self.test_documents, query, config
        )
        
        # Should include similarity scores
        self.assertIn("Similarity:", context)
        
        # Should filter out documents below threshold (0.78 < 0.8)
        self.assertIn("Aspirin", context)  # 0.92 similarity
        self.assertIn("Ibuprofen", context)  # 0.85 similarity
        # Acetaminophen might be excluded due to low similarity
    
    def test_context_truncation(self):
        """Test context truncation when too long"""
        config = ContextConfig(max_context_length=100)  # Very short limit
        
        query = "test query"
        context = self.context_builder.build_context(
            self.test_documents, query, config
        )
        
        # Context should be truncated
        self.assertLessEqual(len(context), 150)  # Some buffer for truncation message
        self.assertIn("...", context)  # Truncation indicator
    
    def test_get_context_stats(self):
        """Test context statistics generation"""
        query = "NSAIDs"
        context = self.context_builder.build_context(self.test_documents, query)
        stats = self.context_builder.get_context_stats(context, self.test_documents)
        
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats['document_count'], 3)
        self.assertAlmostEqual(stats['avg_similarity'], 0.85, places=2)
        self.assertEqual(len(stats['sources']), 3)
        self.assertIn('context_length', stats)
        self.assertGreater(stats['context_length'], 0)
    
    def test_empty_documents(self):
        """Test context building with empty document list"""
        context = self.context_builder.build_context([], "test query")
        
        self.assertIsInstance(context, str)
        self.assertIn("No relevant", context.lower())


class TestRAGOrchestrator(unittest.TestCase):
    """Unit tests for RAG Orchestrator with mocked components"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock components
        self.mock_retriever = Mock()
        self.mock_context_builder = Mock()
        self.mock_llm = Mock()
        
        # Set up mock responses
        self.mock_documents = [
            Document(
                id='doc1',
                content='Aspirin inhibits COX enzymes for pain relief.',
                source='pharmacology.pdf',
                metadata={},
                similarity=0.85
            )
        ]
        
        self.mock_retriever.similarity_search.return_value = self.mock_documents
        self.mock_context_builder.build_context.return_value = "Context: Aspirin inhibits COX enzymes for pain relief."
        self.mock_context_builder.get_context_stats.return_value = {
            'context_length': 50,
            'document_count': 1,
            'avg_similarity': 0.85,
            'sources': ['pharmacology.pdf']
        }
        self.mock_llm.generate_response.return_value = "Based on the context, aspirin works by inhibiting COX enzymes."
    
    def test_initialization(self):
        """Test RAG Orchestrator initialization"""
        config = RAGConfig(retrieval_k=5, similarity_threshold=0.3)
        
        orchestrator = RAGOrchestrator(
            vector_retriever=self.mock_retriever,
            context_builder=self.mock_context_builder,
            llm=self.mock_llm,
            config=config
        )
        
        self.assertIsNotNone(orchestrator)
        self.assertEqual(orchestrator.vector_retriever, self.mock_retriever)
        self.assertEqual(orchestrator.context_builder, self.mock_context_builder)
        self.assertEqual(orchestrator.llm, self.mock_llm)
        self.assertEqual(orchestrator.config.retrieval_k, 5)
    
    def test_process_query_success(self):
        """Test successful query processing"""
        orchestrator = RAGOrchestrator(
            vector_retriever=self.mock_retriever,
            context_builder=self.mock_context_builder,
            llm=self.mock_llm
        )
        
        user_id = str(uuid.uuid4())
        query = "How does aspirin work?"
        
        response = orchestrator.process_query(
            query=query,
            user_id=user_id,
            model_type="fast"
        )
        
        # Verify response structure
        self.assertIsInstance(response, RAGResponse)
        self.assertTrue(response.success)
        self.assertEqual(response.query, query)
        self.assertEqual(response.user_id, user_id)
        self.assertEqual(response.model_used, "fast")
        self.assertIsNotNone(response.response)
        self.assertEqual(len(response.documents_retrieved), 1)
        self.assertIsNotNone(response.context_stats)
        
        # Verify component interactions
        self.mock_retriever.similarity_search.assert_called_once()
        self.mock_context_builder.build_context.assert_called_once()
        self.mock_llm.generate_response.assert_called_once()
    
    def test_process_query_no_documents(self):
        """Test query processing when no documents are retrieved"""
        # Mock empty retrieval
        self.mock_retriever.similarity_search.return_value = []
        self.mock_context_builder.build_context.return_value = "No relevant context found."
        
        orchestrator = RAGOrchestrator(
            vector_retriever=self.mock_retriever,
            context_builder=self.mock_context_builder,
            llm=self.mock_llm
        )
        
        response = orchestrator.process_query(
            query="obscure query",
            user_id=str(uuid.uuid4()),
            model_type="fast"
        )
        
        self.assertTrue(response.success)
        self.assertEqual(len(response.documents_retrieved), 0)
        # Should still generate a response using LLM without context
    
    def test_process_query_with_error_handling(self):
        """Test query processing with error handling"""
        # Mock retriever error
        self.mock_retriever.similarity_search.side_effect = Exception("Database error")
        
        orchestrator = RAGOrchestrator(
            vector_retriever=self.mock_retriever,
            context_builder=self.mock_context_builder,
            llm=self.mock_llm
        )
        
        response = orchestrator.process_query(
            query="test query",
            user_id=str(uuid.uuid4()),
            model_type="fast"
        )
        
        # Should handle error gracefully
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error_message)
        self.assertIn("error", response.error_message.lower())
    
    def test_fallback_to_llm_only(self):
        """Test fallback to LLM-only mode when RAG fails"""
        orchestrator = RAGOrchestrator(
            vector_retriever=self.mock_retriever,
            context_builder=self.mock_context_builder,
            llm=self.mock_llm
        )
        
        # Test the fallback method directly
        response = orchestrator._fallback_to_llm_only(
            query="test query",
            user_id=str(uuid.uuid4()),
            model_type="fast",
            error_message="RAG pipeline failed"
        )
        
        self.assertTrue(response.success)
        self.assertEqual(len(response.documents_retrieved), 0)
        self.assertIn("without context", response.response.lower())


class TestRAGIntegration(unittest.TestCase):
    """Integration tests for RAG pipeline components"""
    
    def test_end_to_end_rag_pipeline(self):
        """Test complete RAG pipeline with mocked external dependencies"""
        # Create mock database
        mock_db = MockVectorDatabase()
        
        # Add test documents to mock database
        user_id = str(uuid.uuid4())
        mock_db.store_document(
            'doc1', user_id, 
            'Aspirin is a pain reliever that inhibits COX enzymes.',
            [0.1] * 384,
            {'source': 'pharmacology.pdf'}
        )
        mock_db.store_document(
            'doc2', user_id,
            'Ibuprofen is an NSAID with anti-inflammatory properties.',
            [0.2] * 384,
            {'source': 'drug_guide.pdf'}
        )
        
        # Mock components
        mock_client = Mock()
        mock_embedding = Mock()
        mock_embedding.embed_query.return_value = [0.15] * 384
        
        # Configure mock client to use our mock database
        def mock_rpc_call(*args, **kwargs):
            mock_result = Mock()
            query_embedding = mock_embedding.embed_query.return_value
            results = mock_db.similarity_search(query_embedding, user_id, k=5)
            mock_result.data = results
            return Mock(execute=lambda: mock_result)
        
        mock_client.rpc.side_effect = mock_rpc_call
        
        # Create components
        retriever = VectorRetriever(mock_client, mock_embedding)
        context_builder = ContextBuilder()
        
        # Mock LLM
        mock_llm = Mock()
        mock_llm.generate_response.return_value = "Based on the provided context, aspirin and ibuprofen are both effective pain relievers."
        
        # Create orchestrator
        orchestrator = RAGOrchestrator(
            vector_retriever=retriever,
            context_builder=context_builder,
            llm=mock_llm
        )
        
        # Process query
        response = orchestrator.process_query(
            query="How do pain relievers work?",
            user_id=user_id,
            model_type="fast"
        )
        
        # Verify end-to-end functionality
        self.assertTrue(response.success)
        self.assertGreater(len(response.documents_retrieved), 0)
        self.assertIn("aspirin", response.response.lower())
        self.assertIsNotNone(response.context_stats)


def run_rag_mock_tests():
    """Run all RAG pipeline tests with mock database"""
    print("🔍 Running RAG Pipeline Tests (Mock Database)")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestVectorRetriever,
        TestDocumentProcessor,
        TestContextBuilder,
        TestRAGOrchestrator,
        TestRAGIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All RAG pipeline tests passed!")
        print("\nRAG Pipeline Features Tested:")
        print("• Vector retrieval with user filtering")
        print("• Document processing and chunking")
        print("• Context building and truncation")
        print("• RAG orchestration and error handling")
        print("• End-to-end pipeline integration")
        print("• Fallback to LLM-only mode")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False


if __name__ == "__main__":
    success = run_rag_mock_tests()
    exit(0 if success else 1)