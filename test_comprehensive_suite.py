"""
Comprehensive Testing Suite for Pharmacology Chat App
Covers all major components with unit tests, integration tests, and UI tests
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all components to test
from auth_manager import AuthenticationManager, AuthResult, User
from session_manager import SessionManager, UserSession
from theme_manager import ThemeManager, ThemeConfig
from ui_components import ChatInterface, AuthInterface, Message
from message_store import MessageStore
from chat_manager import ChatManager
from vector_retriever import VectorRetriever, Document
from rag_orchestrator import RAGOrchestrator
from model_manager import ModelManager


class TestRunner:
    """Main test runner for the comprehensive test suite"""
    
    def __init__(self):
        self.test_results = {
            'auth_tests': {'passed': 0, 'failed': 0, 'errors': []},
            'session_tests': {'passed': 0, 'failed': 0, 'errors': []},
            'ui_tests': {'passed': 0, 'failed': 0, 'errors': []},
            'integration_tests': {'passed': 0, 'failed': 0, 'errors': []},
            'rag_tests': {'passed': 0, 'failed': 0, 'errors': []}
        }
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🧪 Running Comprehensive Test Suite")
        print("=" * 60)
        
        # Run each test suite
        self._run_auth_tests()
        self._run_session_tests()
        self._run_ui_tests()
        self._run_integration_tests()
        self._run_rag_tests()
        
        # Print summary
        self._print_summary()
        
        return self._get_overall_success()
    
    def _run_auth_tests(self):
        """Run authentication manager tests"""
        print("\n🔐 Authentication Manager Tests")
        print("-" * 40)
        
        auth_tester = AuthenticationTests()
        try:
            auth_tester.test_auth_manager_initialization()
            self.test_results['auth_tests']['passed'] += 1
            print("✅ Auth manager initialization")
        except Exception as e:
            self.test_results['auth_tests']['failed'] += 1
            self.test_results['auth_tests']['errors'].append(f"Auth init: {str(e)}")
            print(f"❌ Auth manager initialization: {str(e)}")
        
        try:
            auth_tester.test_sign_up_validation()
            self.test_results['auth_tests']['passed'] += 1
            print("✅ Sign up validation")
        except Exception as e:
            self.test_results['auth_tests']['failed'] += 1
            self.test_results['auth_tests']['errors'].append(f"Sign up validation: {str(e)}")
            print(f"❌ Sign up validation: {str(e)}")
        
        try:
            auth_tester.test_sign_in_validation()
            self.test_results['auth_tests']['passed'] += 1
            print("✅ Sign in validation")
        except Exception as e:
            self.test_results['auth_tests']['failed'] += 1
            self.test_results['auth_tests']['errors'].append(f"Sign in validation: {str(e)}")
            print(f"❌ Sign in validation: {str(e)}")
        
        try:
            auth_tester.test_session_validation()
            self.test_results['auth_tests']['passed'] += 1
            print("✅ Session validation")
        except Exception as e:
            self.test_results['auth_tests']['failed'] += 1
            self.test_results['auth_tests']['errors'].append(f"Session validation: {str(e)}")
            print(f"❌ Session validation: {str(e)}")
    
    def _run_session_tests(self):
        """Run session manager tests"""
        print("\n🔄 Session Manager Tests")
        print("-" * 40)
        
        session_tester = SessionManagerTests()
        try:
            session_tester.test_session_initialization()
            self.test_results['session_tests']['passed'] += 1
            print("✅ Session initialization")
        except Exception as e:
            self.test_results['session_tests']['failed'] += 1
            self.test_results['session_tests']['errors'].append(f"Session init: {str(e)}")
            print(f"❌ Session initialization: {str(e)}")
        
        try:
            session_tester.test_preference_management()
            self.test_results['session_tests']['passed'] += 1
            print("✅ Preference management")
        except Exception as e:
            self.test_results['session_tests']['failed'] += 1
            self.test_results['session_tests']['errors'].append(f"Preference mgmt: {str(e)}")
            print(f"❌ Preference management: {str(e)}")
        
        try:
            session_tester.test_session_validation()
            self.test_results['session_tests']['passed'] += 1
            print("✅ Session validation")
        except Exception as e:
            self.test_results['session_tests']['failed'] += 1
            self.test_results['session_tests']['errors'].append(f"Session validation: {str(e)}")
            print(f"❌ Session validation: {str(e)}")
    
    def _run_ui_tests(self):
        """Run UI component tests"""
        print("\n🎨 UI Component Tests")
        print("-" * 40)
        
        ui_tester = UIComponentTests()
        try:
            ui_tester.test_theme_manager()
            self.test_results['ui_tests']['passed'] += 1
            print("✅ Theme manager")
        except Exception as e:
            self.test_results['ui_tests']['failed'] += 1
            self.test_results['ui_tests']['errors'].append(f"Theme manager: {str(e)}")
            print(f"❌ Theme manager: {str(e)}")
        
        try:
            ui_tester.test_chat_interface()
            self.test_results['ui_tests']['passed'] += 1
            print("✅ Chat interface")
        except Exception as e:
            self.test_results['ui_tests']['failed'] += 1
            self.test_results['ui_tests']['errors'].append(f"Chat interface: {str(e)}")
            print(f"❌ Chat interface: {str(e)}")
        
        try:
            ui_tester.test_responsive_design()
            self.test_results['ui_tests']['passed'] += 1
            print("✅ Responsive design")
        except Exception as e:
            self.test_results['ui_tests']['failed'] += 1
            self.test_results['ui_tests']['errors'].append(f"Responsive design: {str(e)}")
            print(f"❌ Responsive design: {str(e)}")
    
    def _run_integration_tests(self):
        """Run integration tests"""
        print("\n🔗 Integration Tests")
        print("-" * 40)
        
        integration_tester = IntegrationTests()
        try:
            integration_tester.test_user_data_isolation()
            self.test_results['integration_tests']['passed'] += 1
            print("✅ User data isolation")
        except Exception as e:
            self.test_results['integration_tests']['failed'] += 1
            self.test_results['integration_tests']['errors'].append(f"Data isolation: {str(e)}")
            print(f"❌ User data isolation: {str(e)}")
        
        try:
            integration_tester.test_auth_chat_integration()
            self.test_results['integration_tests']['passed'] += 1
            print("✅ Auth-chat integration")
        except Exception as e:
            self.test_results['integration_tests']['failed'] += 1
            self.test_results['integration_tests']['errors'].append(f"Auth-chat integration: {str(e)}")
            print(f"❌ Auth-chat integration: {str(e)}")
        
        try:
            integration_tester.test_end_to_end_flow()
            self.test_results['integration_tests']['passed'] += 1
            print("✅ End-to-end flow")
        except Exception as e:
            self.test_results['integration_tests']['failed'] += 1
            self.test_results['integration_tests']['errors'].append(f"E2E flow: {str(e)}")
            print(f"❌ End-to-end flow: {str(e)}")
    
    def _run_rag_tests(self):
        """Run RAG pipeline tests"""
        print("\n🔍 RAG Pipeline Tests")
        print("-" * 40)
        
        rag_tester = RAGPipelineTests()
        try:
            rag_tester.test_vector_retrieval()
            self.test_results['rag_tests']['passed'] += 1
            print("✅ Vector retrieval")
        except Exception as e:
            self.test_results['rag_tests']['failed'] += 1
            self.test_results['rag_tests']['errors'].append(f"Vector retrieval: {str(e)}")
            print(f"❌ Vector retrieval: {str(e)}")
        
        try:
            rag_tester.test_context_building()
            self.test_results['rag_tests']['passed'] += 1
            print("✅ Context building")
        except Exception as e:
            self.test_results['rag_tests']['failed'] += 1
            self.test_results['rag_tests']['errors'].append(f"Context building: {str(e)}")
            print(f"❌ Context building: {str(e)}")
        
        try:
            rag_tester.test_orchestrator_integration()
            self.test_results['rag_tests']['passed'] += 1
            print("✅ RAG orchestrator")
        except Exception as e:
            self.test_results['rag_tests']['failed'] += 1
            self.test_results['rag_tests']['errors'].append(f"RAG orchestrator: {str(e)}")
            print(f"❌ RAG orchestrator: {str(e)}")
    
    def _print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        total_passed = 0
        total_failed = 0
        
        for suite_name, results in self.test_results.items():
            passed = results['passed']
            failed = results['failed']
            total_passed += passed
            total_failed += failed
            
            status = "✅" if failed == 0 else "❌"
            print(f"{status} {suite_name.replace('_', ' ').title()}: {passed} passed, {failed} failed")
            
            if results['errors']:
                for error in results['errors']:
                    print(f"   • {error}")
        
        print("-" * 60)
        print(f"Total: {total_passed} passed, {total_failed} failed")
        
        if total_failed == 0:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {total_failed} tests failed")
    
    def _get_overall_success(self) -> bool:
        """Check if all tests passed"""
        for results in self.test_results.values():
            if results['failed'] > 0:
                return False
        return True


class AuthenticationTests:
    """Unit tests for authentication manager"""
    
    def test_auth_manager_initialization(self):
        """Test authentication manager can be initialized"""
        with patch('streamlit.secrets', {'SUPABASE_URL': 'test_url', 'SUPABASE_ANON_KEY': 'test_key'}):
            with patch('supabase.create_client') as mock_create:
                mock_client = Mock()
                mock_client.auth.get_session.return_value = None
                mock_create.return_value = mock_client
                
                auth_manager = AuthenticationManager()
                assert auth_manager is not None
                assert auth_manager.supabase_url == 'test_url'
                assert auth_manager.supabase_key == 'test_key'
    
    def test_sign_up_validation(self):
        """Test sign up input validation"""
        with patch('streamlit.secrets', {'SUPABASE_URL': 'test_url', 'SUPABASE_ANON_KEY': 'test_key'}):
            with patch('supabase.create_client') as mock_create:
                mock_client = Mock()
                mock_client.auth.get_session.return_value = None
                mock_create.return_value = mock_client
                
                auth_manager = AuthenticationManager()
                
                # Test empty email/password
                result = auth_manager.sign_up("", "password")
                assert result.success is False
                assert "required" in result.error_message.lower()
                
                # Test short password
                result = auth_manager.sign_up("test@example.com", "123")
                assert result.success is False
                assert "6 characters" in result.error_message
    
    def test_sign_in_validation(self):
        """Test sign in input validation"""
        with patch('streamlit.secrets', {'SUPABASE_URL': 'test_url', 'SUPABASE_ANON_KEY': 'test_key'}):
            with patch('supabase.create_client') as mock_create:
                mock_client = Mock()
                mock_client.auth.get_session.return_value = None
                mock_create.return_value = mock_client
                
                auth_manager = AuthenticationManager()
                
                # Test empty credentials
                result = auth_manager.sign_in("", "")
                assert result.success is False
                assert "required" in result.error_message.lower()
    
    def test_session_validation(self):
        """Test session validation logic"""
        with patch('streamlit.secrets', {'SUPABASE_URL': 'test_url', 'SUPABASE_ANON_KEY': 'test_key'}):
            with patch('supabase.create_client') as mock_create:
                mock_client = Mock()
                mock_client.auth.get_session.return_value = None
                mock_create.return_value = mock_client
                
                auth_manager = AuthenticationManager()
                
                # Test with no user
                mock_client.auth.get_user.return_value.user = None
                result = auth_manager.validate_session()
                assert result is False


class SessionManagerTests:
    """Unit tests for session manager"""
    
    def test_session_initialization(self):
        """Test session manager initialization"""
        mock_auth_manager = Mock()
        session_manager = SessionManager(mock_auth_manager)
        
        assert session_manager.auth_manager == mock_auth_manager
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_preference_management(self, mock_session_state):
        """Test preference management"""
        mock_auth_manager = Mock()
        session_manager = SessionManager(mock_auth_manager)
        
        # Initialize session
        session_manager.initialize_session("user123", "test@example.com", {"theme": "dark"})
        
        # Test preference updates
        session_manager.update_theme("light")
        assert mock_session_state['theme'] == "light"
        
        session_manager.update_model_preference("premium")
        assert mock_session_state['model_preference'] == "premium"
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_session_validation(self, mock_session_state):
        """Test session validation"""
        mock_auth_manager = Mock()
        mock_auth_manager.get_current_user.return_value = Mock(id="user123")
        
        session_manager = SessionManager(mock_auth_manager)
        session_manager.initialize_session("user123", "test@example.com")
        
        # Test valid session
        result = session_manager.validate_session()
        assert result is True
        
        # Test invalid session
        mock_auth_manager.get_current_user.return_value = None
        result = session_manager.validate_session()
        assert result is False


class UIComponentTests:
    """Unit tests for UI components"""
    
    def test_theme_manager(self):
        """Test theme manager functionality"""
        theme_manager = ThemeManager()
        
        # Test theme switching
        initial_theme = theme_manager.get_current_theme()
        toggled_theme = theme_manager.toggle_theme()
        
        assert toggled_theme != initial_theme
        assert toggled_theme in ["light", "dark"]
        
        # Test theme configuration
        config = theme_manager.get_theme_config("light")
        assert isinstance(config, ThemeConfig)
        assert config.name == "light"
        
        # Test CSS generation
        css = theme_manager._generate_css(config)
        assert "background-color" in css
        assert "color" in css
    
    def test_chat_interface(self):
        """Test chat interface components"""
        mock_theme_manager = Mock()
        chat_interface = ChatInterface(mock_theme_manager)
        
        # Test message formatting
        test_message = Message(
            role="user",
            content="Test message with **bold** text",
            timestamp=datetime.now()
        )
        
        # This would normally render HTML, but we can test the component exists
        assert chat_interface is not None
        assert hasattr(chat_interface, 'render_message_bubble')
        assert hasattr(chat_interface, 'render_chat_history')
    
    def test_responsive_design(self):
        """Test responsive design utilities"""
        from ui_components import ResponsiveLayout
        
        # Test layout configuration
        config = ResponsiveLayout.get_layout_config()
        assert isinstance(config, dict)
        assert 'sidebar_width' in config
        assert 'mobile_breakpoint' in config
        
        # Test responsive CSS generation
        css = ResponsiveLayout.apply_responsive_css()
        assert "@media" in css
        assert "max-width" in css


class IntegrationTests:
    """Integration tests for component interactions"""
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_user_data_isolation(self, mock_session_state):
        """Test that user data is properly isolated"""
        # Mock Supabase client
        mock_client = Mock()
        
        # Create session managers for different users
        mock_auth_manager1 = Mock()
        mock_auth_manager1.get_current_user.return_value = Mock(id="user1")
        session_manager1 = SessionManager(mock_auth_manager1)
        
        mock_auth_manager2 = Mock()
        mock_auth_manager2.get_current_user.return_value = Mock(id="user2")
        session_manager2 = SessionManager(mock_auth_manager2)
        
        # Initialize sessions
        session_manager1.initialize_session("user1", "user1@example.com")
        session_manager2.initialize_session("user2", "user2@example.com")
        
        # Test that users have different session data
        assert session_manager1.get_user_id() != session_manager2.get_user_id()
        
        # Test chat manager isolation
        chat_manager1 = ChatManager(mock_client, session_manager1)
        chat_manager2 = ChatManager(mock_client, session_manager2)
        
        # User 1 should not be able to access user 2's data
        assert chat_manager1.validate_user_access("user2") is False
        assert chat_manager2.validate_user_access("user1") is False
        
        # Users should be able to access their own data
        assert chat_manager1.validate_user_access("user1") is True
        assert chat_manager2.validate_user_access("user2") is True
    
    def test_auth_chat_integration(self):
        """Test authentication and chat system integration"""
        # Mock components
        mock_client = Mock()
        mock_auth_manager = Mock()
        mock_auth_manager.get_current_user.return_value = Mock(id="user123")
        
        session_manager = SessionManager(mock_auth_manager)
        chat_manager = ChatManager(mock_client, session_manager)
        
        # Test that chat requires authentication
        with patch('streamlit.session_state', {}):
            response = chat_manager.send_message("user123", "test message")
            assert response.success is False
            assert "not authenticated" in response.error_message.lower()
    
    def test_end_to_end_flow(self):
        """Test complete user flow from auth to chat"""
        # This is a simplified end-to-end test
        with patch('streamlit.secrets', {'SUPABASE_URL': 'test_url', 'SUPABASE_ANON_KEY': 'test_key'}):
            with patch('supabase.create_client') as mock_create:
                mock_client = Mock()
                mock_client.auth.get_session.return_value = None
                mock_create.return_value = mock_client
                
                # Initialize components
                auth_manager = AuthenticationManager()
                session_manager = SessionManager(auth_manager)
                theme_manager = ThemeManager()
                
                # Test component integration
                assert auth_manager is not None
                assert session_manager is not None
                assert theme_manager is not None
                
                # Test theme application
                theme_manager.apply_theme("light")
                current_theme = theme_manager.get_current_theme()
                assert current_theme in ["light", "dark"]


class RAGPipelineTests:
    """Tests for RAG pipeline with mock vector database"""
    
    def test_vector_retrieval(self):
        """Test vector retrieval with mock database"""
        # Mock Supabase client
        mock_client = Mock()
        mock_client.rpc.return_value.execute.return_value.data = [
            {
                'id': 'doc1',
                'content': 'Test pharmacology content',
                'source': 'test.pdf',
                'metadata': {},
                'similarity': 0.85
            }
        ]
        
        # Mock embedding model
        mock_embedding = Mock()
        mock_embedding.embed_query.return_value = [0.1] * 384
        
        retriever = VectorRetriever(supabase_client=mock_client, embedding_model=mock_embedding)
        
        # Test retrieval
        documents = retriever.similarity_search("test query", "user123", k=5)
        
        assert len(documents) == 1
        assert documents[0].content == 'Test pharmacology content'
        assert documents[0].similarity == 0.85
    
    def test_context_building(self):
        """Test context building from retrieved documents"""
        from context_builder import ContextBuilder
        
        # Create test documents
        documents = [
            Document(
                id='doc1',
                content='Aspirin is a pain reliever.',
                source='test.pdf',
                metadata={},
                similarity=0.85
            ),
            Document(
                id='doc2',
                content='Ibuprofen is an anti-inflammatory.',
                source='test2.pdf',
                metadata={},
                similarity=0.75
            )
        ]
        
        builder = ContextBuilder()
        context = builder.build_context(documents, "pain relief")
        
        assert len(context) > 0
        assert 'Aspirin' in context
        assert 'Ibuprofen' in context
    
    def test_orchestrator_integration(self):
        """Test RAG orchestrator with mocked components"""
        # Mock components
        mock_retriever = Mock()
        mock_retriever.similarity_search.return_value = [
            Document(
                id='doc1',
                content='Test content',
                source='test.pdf',
                metadata={},
                similarity=0.85
            )
        ]
        
        mock_context_builder = Mock()
        mock_context_builder.build_context.return_value = "Test context"
        mock_context_builder.get_context_stats.return_value = {
            'context_length': 50,
            'document_count': 1,
            'avg_similarity': 0.85
        }
        
        mock_llm = Mock()
        mock_llm.generate_response.return_value = "Test response"
        
        orchestrator = RAGOrchestrator(
            vector_retriever=mock_retriever,
            context_builder=mock_context_builder,
            llm=mock_llm
        )
        
        # Test query processing
        response = orchestrator.process_query(
            query="test query",
            user_id="user123",
            model_type="fast"
        )
        
        assert response.success is True
        assert response.response == "Test response"
        assert len(response.documents_retrieved) == 1


def main():
    """Main function to run all tests"""
    test_runner = TestRunner()
    success = test_runner.run_all_tests()
    
    if success:
        print("\n🎉 All comprehensive tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())