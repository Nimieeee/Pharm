"""
Test suite for UI Error Handling System
Tests comprehensive error handling for conversation management, document processing, and RAG pipeline failures.
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
import time

from ui_error_handler import UIErrorHandler, UIErrorType, UIErrorContext
from conversation_ui import ConversationUI
from document_ui import DocumentUploadInterface
from rag_orchestrator import RAGOrchestrator


class TestUIErrorHandler:
    """Test the UI Error Handler functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.ui_error_handler = UIErrorHandler()
        self.test_user_id = "test_user_123"
    
    def test_conversation_creation_error_handling(self):
        """Test conversation creation error handling"""
        # Test database connection error
        db_error = ConnectionError("Database connection failed")
        context = UIErrorContext(
            user_id=self.test_user_id,
            action="create_conversation",
            component="ConversationUI"
        )
        
        result = self.ui_error_handler.handle_conversation_error(db_error, context)
        
        assert result['severity'] == 'high'
        assert 'database connectivity' in result['user_message']
        assert len(result['actions']) >= 2
        assert result['fallback_available'] is True
    
    def test_conversation_switching_error_handling(self):
        """Test conversation switching error handling"""
        # Test conversation not found error
        not_found_error = ValueError("Conversation not found")
        context = UIErrorContext(
            user_id=self.test_user_id,
            action="switch_conversation",
            component="ConversationUI"
        )
        
        result = self.ui_error_handler.handle_conversation_error(not_found_error, context)
        
        assert result['severity'] == 'medium'
        assert 'not found' in result['user_message']
        assert len(result['actions']) >= 2
        assert result['fallback_available'] is True
    
    def test_document_upload_error_handling(self):
        """Test document upload error handling"""
        # Test file size error
        size_error = ValueError("File too large")
        context = UIErrorContext(
            user_id=self.test_user_id,
            action="file_upload",
            component="DocumentUploadInterface",
            additional_data={'file_count': 3}
        )
        
        result = self.ui_error_handler.handle_document_processing_error(size_error, context)
        
        assert result['severity'] == 'medium'
        assert 'large' in result['user_message']
        assert result['fallback_available'] is True
    
    def test_document_processing_error_handling(self):
        """Test document processing error handling"""
        # Test processing failure
        processing_error = RuntimeError("Failed to extract text")
        context = UIErrorContext(
            user_id=self.test_user_id,
            action="document_processing",
            component="DocumentProcessor"
        )
        
        result = self.ui_error_handler.handle_document_processing_error(processing_error, context)
        
        assert result['severity'] == 'medium'
        assert 'processing failed' in result['user_message']
        assert result['fallback_available'] is True
    
    def test_rag_retrieval_error_handling(self):
        """Test RAG retrieval error handling"""
        # Test retrieval failure
        retrieval_error = ConnectionError("Vector search failed")
        context = UIErrorContext(
            user_id=self.test_user_id,
            action="rag_retrieval",
            component="RAGOrchestrator"
        )
        
        result = self.ui_error_handler.handle_rag_pipeline_error(retrieval_error, context)
        
        assert result['severity'] == 'low'
        assert 'search' in result['user_message']
        assert result['fallback_available'] is True
    
    def test_rag_context_building_error_handling(self):
        """Test RAG context building error handling"""
        # Test context building failure
        context_error = RuntimeError("Failed to build context")
        context = UIErrorContext(
            user_id=self.test_user_id,
            action="context_building",
            component="RAGOrchestrator"
        )
        
        result = self.ui_error_handler.handle_rag_pipeline_error(context_error, context)
        
        assert result['severity'] == 'low'
        assert 'general knowledge' in result['user_message']
        assert result['fallback_available'] is True
    
    def test_fallback_strategies(self):
        """Test fallback strategy implementations"""
        context = UIErrorContext(
            user_id=self.test_user_id,
            action="test_action",
            component="TestComponent"
        )
        
        # Test conversation creation fallback
        self.ui_error_handler._fallback_conversation_creation(context)
        # Should not raise any exceptions
        
        # Test document processing fallback
        self.ui_error_handler._fallback_document_processing(context)
        # Should not raise any exceptions
        
        # Test RAG retrieval fallback
        self.ui_error_handler._fallback_rag_retrieval(context)
        # Should not raise any exceptions


class TestConversationUIErrorHandling:
    """Test error handling in ConversationUI"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_conversation_manager = Mock()
        self.mock_theme_manager = Mock()
        self.conversation_ui = ConversationUI(
            self.mock_conversation_manager,
            self.mock_theme_manager
        )
    
    @patch('streamlit.session_state', {})
    def test_load_conversations_with_error_handling(self):
        """Test conversation loading with error handling"""
        # Mock conversation manager to raise exception
        self.mock_conversation_manager.get_user_conversations.side_effect = ConnectionError("DB Error")
        
        result = self.conversation_ui._load_conversations_with_error_handling(self.test_user_id)
        
        # Should return empty list on error
        assert result == []
    
    @patch('streamlit.session_state', {})
    def test_create_default_conversation_with_error_handling(self):
        """Test default conversation creation with error handling"""
        # Mock conversation manager to raise exception
        self.mock_conversation_manager.get_or_create_default_conversation.side_effect = RuntimeError("Creation failed")
        
        result = self.conversation_ui._create_default_conversation_with_error_handling(self.test_user_id)
        
        # Should return None on error
        assert result is None
    
    def test_get_current_conversation_id_safely(self):
        """Test safe conversation ID retrieval"""
        # Should not raise exceptions even with missing session state
        result = self.conversation_ui._get_current_conversation_id_safely()
        
        # Should return None if no conversation ID is set
        assert result is None
    
    def test_set_current_conversation_id_safely(self):
        """Test safe conversation ID setting"""
        test_id = "test_conv_123"
        
        # Should not raise exceptions
        result = self.conversation_ui._set_current_conversation_id_safely(test_id)
        
        # Should return True on success
        assert result is True


class TestDocumentUIErrorHandling:
    """Test error handling in Document UI"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_document_manager = Mock()
        self.document_upload_interface = DocumentUploadInterface(self.mock_document_manager)
        self.test_user_id = "test_user_123"
    
    def test_file_upload_error_handling_success(self):
        """Test successful file upload handling"""
        # Mock successful upload
        mock_upload_result = Mock()
        mock_upload_result.success = True
        mock_upload_result.documents_processed = 5
        mock_upload_result.processing_details = ["File 1 processed", "File 2 processed"]
        
        self.mock_document_manager.upload_documents.return_value = mock_upload_result
        
        uploaded_files = [Mock(), Mock()]
        
        with patch('streamlit.success'), patch('streamlit.balloons'), patch('streamlit.expander'):
            result = self.document_upload_interface._handle_file_upload_with_error_handling(
                uploaded_files, self.test_user_id, 1000, 200
            )
        
        assert result.success is True
        assert result.documents_processed == 5
    
    def test_file_upload_error_handling_failure(self):
        """Test file upload error handling on failure"""
        # Mock failed upload
        mock_upload_result = Mock()
        mock_upload_result.success = False
        mock_upload_result.error_message = "File format not supported"
        
        self.mock_document_manager.upload_documents.return_value = mock_upload_result
        
        uploaded_files = [Mock()]
        
        with patch('streamlit.error'), patch('streamlit.warning'):
            result = self.document_upload_interface._handle_file_upload_with_error_handling(
                uploaded_files, self.test_user_id, 1000, 200
            )
        
        assert result.success is False
    
    def test_url_upload_error_handling_success(self):
        """Test successful URL upload handling"""
        # Mock successful URL upload
        mock_upload_result = Mock()
        mock_upload_result.success = True
        mock_upload_result.documents_processed = 3
        mock_upload_result.processing_details = ["URL content extracted"]
        
        self.mock_document_manager.upload_from_url.return_value = mock_upload_result
        
        test_url = "https://example.com/article"
        
        with patch('streamlit.success'), patch('streamlit.balloons'), patch('streamlit.expander'):
            result = self.document_upload_interface._handle_url_upload_with_error_handling(
                test_url, self.test_user_id, 1000, 200
            )
        
        assert result.success is True
        assert result.documents_processed == 3
    
    def test_url_upload_error_handling_network_error(self):
        """Test URL upload handling with network error"""
        # Mock network error
        mock_upload_result = Mock()
        mock_upload_result.success = False
        mock_upload_result.error_message = "Network connection failed"
        
        self.mock_document_manager.upload_from_url.return_value = mock_upload_result
        
        test_url = "https://example.com/article"
        
        with patch('streamlit.error'), patch('streamlit.warning'):
            result = self.document_upload_interface._handle_url_upload_with_error_handling(
                test_url, self.test_user_id, 1000, 200
            )
        
        assert result.success is False


class TestRAGOrchestratorErrorHandling:
    """Test error handling in RAG Orchestrator"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_vector_retriever = Mock()
        self.mock_context_builder = Mock()
        self.mock_llm = Mock()
        
        self.rag_orchestrator = RAGOrchestrator(
            vector_retriever=self.mock_vector_retriever,
            context_builder=self.mock_context_builder,
            llm=self.mock_llm
        )
        self.test_user_id = "test_user_123"
    
    def test_retrieve_documents_with_error_handling_success(self):
        """Test successful document retrieval"""
        mock_documents = [Mock(), Mock()]
        self.mock_vector_retriever.similarity_search.return_value = mock_documents
        
        result = self.rag_orchestrator._retrieve_documents_with_error_handling(
            "test query", self.test_user_id
        )
        
        assert len(result) == 2
    
    def test_retrieve_documents_with_error_handling_failure(self):
        """Test document retrieval with error and fallback"""
        # First call fails, second call (fallback) succeeds
        self.mock_vector_retriever.similarity_search.side_effect = [
            ConnectionError("DB connection failed"),
            [Mock()]  # Fallback succeeds with one document
        ]
        
        result = self.rag_orchestrator._retrieve_documents_with_error_handling(
            "test query", self.test_user_id
        )
        
        assert len(result) == 1
        # Should have been called twice (original + fallback)
        assert self.mock_vector_retriever.similarity_search.call_count == 2
    
    def test_retrieve_documents_complete_failure(self):
        """Test document retrieval when both attempts fail"""
        # Both calls fail
        self.mock_vector_retriever.similarity_search.side_effect = ConnectionError("DB connection failed")
        
        result = self.rag_orchestrator._retrieve_documents_with_error_handling(
            "test query", self.test_user_id
        )
        
        assert result == []
    
    def test_build_context_with_error_handling_success(self):
        """Test successful context building"""
        self.mock_context_builder.build_context.return_value = "Test context"
        
        result = self.rag_orchestrator._build_context_with_error_handling(
            [Mock()], "test query", None
        )
        
        assert result == "Test context"
    
    def test_build_context_with_error_handling_fallback(self):
        """Test context building with error and fallback"""
        # First call fails, use simple fallback
        self.mock_context_builder.build_context.side_effect = RuntimeError("Context building failed")
        
        mock_doc = Mock()
        mock_doc.source = "test_source"
        mock_doc.content = "Test content for fallback"
        
        result = self.rag_orchestrator._build_context_with_error_handling(
            [mock_doc], "test query", None
        )
        
        assert "test_source" in result
        assert "Test content" in result
    
    def test_generate_with_context_safe_success(self):
        """Test successful context-based generation"""
        self.mock_llm.generate_response.return_value = "Test response"
        
        with patch.object(self.rag_orchestrator, '_generate_with_context', return_value="Test response"):
            result = self.rag_orchestrator._generate_with_context_safe(
                "test query", "test context", "fast", None, self.test_user_id
            )
        
        assert result == "Test response"
    
    def test_generate_with_context_safe_fallback(self):
        """Test context-based generation with fallback"""
        # First call fails, fallback to no history
        with patch.object(self.rag_orchestrator, '_generate_with_context') as mock_generate:
            mock_generate.side_effect = [RuntimeError("Generation failed"), "Fallback response"]
            
            result = self.rag_orchestrator._generate_with_context_safe(
                "test query", "test context", "fast", [{"role": "user", "content": "history"}], self.test_user_id
            )
        
        assert result == "Fallback response"
        # Should have been called twice
        assert mock_generate.call_count == 2
    
    def test_get_error_fallback_response(self):
        """Test final error fallback response"""
        result = self.rag_orchestrator._get_error_fallback_response("test query about pharmacology")
        
        assert "technical difficulties" in result
        assert "test query about" in result
        assert "try again" in result


def run_error_handling_tests():
    """Run all error handling tests"""
    print("🧪 Running UI Error Handling Tests...")
    
    # Test UI Error Handler
    print("\n📋 Testing UI Error Handler...")
    test_ui_error_handler = TestUIErrorHandler()
    test_ui_error_handler.setup_method()
    
    try:
        test_ui_error_handler.test_conversation_creation_error_handling()
        print("✅ Conversation creation error handling")
        
        test_ui_error_handler.test_conversation_switching_error_handling()
        print("✅ Conversation switching error handling")
        
        test_ui_error_handler.test_document_upload_error_handling()
        print("✅ Document upload error handling")
        
        test_ui_error_handler.test_document_processing_error_handling()
        print("✅ Document processing error handling")
        
        test_ui_error_handler.test_rag_retrieval_error_handling()
        print("✅ RAG retrieval error handling")
        
        test_ui_error_handler.test_rag_context_building_error_handling()
        print("✅ RAG context building error handling")
        
        test_ui_error_handler.test_fallback_strategies()
        print("✅ Fallback strategies")
        
    except Exception as e:
        print(f"❌ UI Error Handler test failed: {e}")
    
    # Test Conversation UI Error Handling
    print("\n💬 Testing Conversation UI Error Handling...")
    test_conversation_ui = TestConversationUIErrorHandling()
    test_conversation_ui.setup_method()
    
    try:
        test_conversation_ui.test_get_current_conversation_id_safely()
        print("✅ Safe conversation ID retrieval")
        
        test_conversation_ui.test_set_current_conversation_id_safely()
        print("✅ Safe conversation ID setting")
        
    except Exception as e:
        print(f"❌ Conversation UI error handling test failed: {e}")
    
    # Test Document UI Error Handling
    print("\n📄 Testing Document UI Error Handling...")
    test_document_ui = TestDocumentUIErrorHandling()
    test_document_ui.setup_method()
    
    try:
        test_document_ui.test_file_upload_error_handling_success()
        print("✅ File upload success handling")
        
        test_document_ui.test_url_upload_error_handling_success()
        print("✅ URL upload success handling")
        
    except Exception as e:
        print(f"❌ Document UI error handling test failed: {e}")
    
    # Test RAG Orchestrator Error Handling
    print("\n🔍 Testing RAG Orchestrator Error Handling...")
    test_rag_orchestrator = TestRAGOrchestratorErrorHandling()
    test_rag_orchestrator.setup_method()
    
    try:
        test_rag_orchestrator.test_retrieve_documents_with_error_handling_success()
        print("✅ Document retrieval success")
        
        test_rag_orchestrator.test_retrieve_documents_complete_failure()
        print("✅ Document retrieval complete failure handling")
        
        test_rag_orchestrator.test_build_context_with_error_handling_success()
        print("✅ Context building success")
        
        test_rag_orchestrator.test_get_error_fallback_response()
        print("✅ Error fallback response")
        
    except Exception as e:
        print(f"❌ RAG Orchestrator error handling test failed: {e}")
    
    print("\n🎉 Error handling tests completed!")


if __name__ == "__main__":
    run_error_handling_tests()