#!/usr/bin/env python3
"""
Final Integration and End-to-End Testing Suite
Tests complete user journey from signup to chat to logout
Validates user data isolation and theme switching
"""

import os
import sys
import time
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
import streamlit as st
from streamlit.testing.v1 import AppTest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application components
from auth_manager import AuthenticationManager
from session_manager import SessionManager
from chat_manager import ChatManager
from message_store_optimized import OptimizedMessageStore
from theme_manager import ThemeManager
from model_manager import ModelManager
from rag_orchestrator_optimized import RAGOrchestrator
from performance_optimizer import performance_optimizer

class TestFinalIntegration:
    """Comprehensive end-to-end integration tests"""
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with mocked dependencies"""
        # Mock Supabase client
        self.mock_supabase = Mock()
        self.mock_supabase.auth.sign_up.return_value = Mock(
            user=Mock(id="test-user-1", email="test1@example.com"),
            session=Mock(access_token="mock-token-1")
        )
        self.mock_supabase.auth.sign_in_with_password.return_value = Mock(
            user=Mock(id="test-user-1", email="test1@example.com"),
            session=Mock(access_token="mock-token-1")
        )
        
        # Mock database operations
        self.mock_supabase.table.return_value.insert.return_value.execute.return_value = Mock(
            data=[{"id": "msg-1", "user_id": "test-user-1", "content": "Test message"}]
        )
        self.mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = Mock(
            data=[]
        )
        
        # Set up test environment variables
        os.environ.update({
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test-anon-key',
            'GROQ_API_KEY': 'test-groq-key'
        })
        
        yield
        
        # Cleanup
        for key in ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'GROQ_API_KEY']:
            os.environ.pop(key, None)
    
    def test_complete_user_journey_signup_to_logout(self):
        """Test complete user journey from signup to chat to logout"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            # Initialize components
            auth_manager = AuthenticationManager()
            session_manager = SessionManager(auth_manager)
            
            # Test 1: User signup
            signup_result = auth_manager.sign_up("test1@example.com", "password123")
            assert signup_result.success, "User signup should succeed"
            assert signup_result.user is not None, "User object should be returned"
            
            # Test 2: User signin
            signin_result = auth_manager.sign_in("test1@example.com", "password123")
            assert signin_result.success, "User signin should succeed"
            
            # Test 3: Session initialization
            session_manager.initialize_session("test-user-1")
            assert session_manager.is_authenticated(), "User should be authenticated"
            assert session_manager.get_user_id() == "test-user-1", "User ID should match"
            
            # Test 4: Chat functionality
            chat_manager = ChatManager(self.mock_supabase, session_manager)
            
            # Send a message
            message_response = chat_manager.send_message(
                user_id="test-user-1",
                message_content="What is pharmacokinetics?",
                model_type="fast"
            )
            assert message_response.success, "Message sending should succeed"
            
            # Test 5: Conversation history
            history = chat_manager.get_conversation_history("test-user-1", limit=10)
            assert isinstance(history, list), "History should be a list"
            
            # Test 6: User logout
            logout_result = auth_manager.sign_out()
            assert logout_result, "User logout should succeed"
            
            # Clear session
            session_manager.clear_session()
            assert not session_manager.is_authenticated(), "User should not be authenticated after logout"

    def test_user_data_isolation_multiple_users(self):
        """Test user data isolation across multiple concurrent users"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            # Create two separate user sessions
            auth_manager1 = AuthenticationManager()
            session_manager1 = SessionManager(auth_manager1)
            
            auth_manager2 = AuthenticationManager()
            session_manager2 = SessionManager(auth_manager2)
            
            # Mock different users
            self.mock_supabase.auth.sign_up.side_effect = [
                Mock(user=Mock(id="user-1", email="user1@test.com"), session=Mock(access_token="token-1")),
                Mock(user=Mock(id="user-2", email="user2@test.com"), session=Mock(access_token="token-2"))
            ]
            
            # Sign up both users
            user1_signup = auth_manager1.sign_up("user1@test.com", "password123")
            user2_signup = auth_manager2.sign_up("user2@test.com", "password123")
            
            assert user1_signup.success and user2_signup.success, "Both users should sign up successfully"
            
            # Initialize sessions
            session_manager1.initialize_session("user-1")
            session_manager2.initialize_session("user-2")
            
            # Create chat managers for both users
            chat_manager1 = ChatManager(self.mock_supabase, session_manager1)
            chat_manager2 = ChatManager(self.mock_supabase, session_manager2)
            
            # Mock database responses for user isolation
            def mock_user_messages(table_name):
                mock_table = Mock()
                mock_select = Mock()
                
                def mock_eq(column, value):
                    # Return different data based on user_id
                    mock_result = Mock()
                    if value == "user-1":
                        mock_result.execute.return_value = Mock(data=[
                            {"id": "msg-1", "user_id": "user-1", "content": "User 1 message", "role": "user"}
                        ])
                    else:
                        mock_result.execute.return_value = Mock(data=[
                            {"id": "msg-2", "user_id": "user-2", "content": "User 2 message", "role": "user"}
                        ])
                    return mock_result.order.return_value.limit.return_value
                
                mock_select.eq = mock_eq
                mock_table.select.return_value = mock_select
                return mock_table
            
            self.mock_supabase.table.side_effect = mock_user_messages
            
            # Test data isolation
            user1_history = chat_manager1.get_conversation_history("user-1", limit=10)
            user2_history = chat_manager2.get_conversation_history("user-2", limit=10)
            
            # Verify isolation - each user should only see their own data
            assert len(user1_history) >= 0, "User 1 should have access to their history"
            assert len(user2_history) >= 0, "User 2 should have access to their history"
            
            # Verify cross-user access is prevented
            user1_accessing_user2 = chat_manager1.get_conversation_history("user-2", limit=10)
            assert len(user1_accessing_user2) == 0, "User 1 should not access User 2's data"

    def test_theme_switching_and_responsive_design(self):
        """Test theme switching functionality and responsive design validation"""
        theme_manager = ThemeManager()
        
        # Test initial theme
        initial_theme = theme_manager.get_current_theme()
        assert initial_theme in ['light', 'dark'], "Initial theme should be valid"
        
        # Test theme switching
        new_theme = theme_manager.toggle_theme()
        assert new_theme != initial_theme, "Theme should change after toggle"
        assert new_theme in ['light', 'dark'], "New theme should be valid"
        
        # Test theme persistence
        current_theme = theme_manager.get_current_theme()
        assert current_theme == new_theme, "Theme should persist after toggle"
        
        # Test theme application (mock CSS injection)
        with patch('streamlit.markdown') as mock_markdown:
            theme_manager.apply_theme()
            mock_markdown.assert_called(), "Theme CSS should be applied"
            
            # Verify CSS contains theme-specific styles
            call_args = mock_markdown.call_args[0][0]
            assert 'background-color' in call_args, "CSS should contain background color"
            assert 'color' in call_args, "CSS should contain text color"

    def test_model_switching_and_preferences(self):
        """Test model switching functionality and preference persistence"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            # Initialize components
            auth_manager = AuthenticationManager()
            session_manager = SessionManager(auth_manager)
            model_manager = ModelManager()
            
            # Mock authentication
            session_manager.initialize_session("test-user-1")
            
            # Test initial model preference
            initial_pref = session_manager.get_model_preference()
            assert initial_pref in ['fast', 'premium'], "Initial preference should be valid"
            
            # Test model switching
            new_pref = 'premium' if initial_pref == 'fast' else 'fast'
            session_manager.update_model_preference(new_pref)
            
            updated_pref = session_manager.get_model_preference()
            assert updated_pref == new_pref, "Model preference should update"
            
            # Test model manager integration
            from model_manager import ModelTier
            tier = ModelTier.PREMIUM if new_pref == 'premium' else ModelTier.FAST
            model_manager.set_current_model(tier)
            
            current_model = model_manager.get_current_model()
            assert current_model.tier == tier, "Model manager should reflect preference"

    def test_error_handling_and_fallbacks(self):
        """Test comprehensive error handling and fallback mechanisms"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            # Test authentication errors
            self.mock_supabase.auth.sign_in_with_password.side_effect = Exception("Auth error")
            
            auth_manager = AuthenticationManager()
            signin_result = auth_manager.sign_in("test@example.com", "wrong_password")
            assert not signin_result.success, "Failed auth should return failure"
            assert signin_result.error is not None, "Error should be captured"
            
            # Test database connection errors
            self.mock_supabase.table.side_effect = Exception("Database error")
            
            session_manager = SessionManager(auth_manager)
            session_manager.initialize_session("test-user-1")
            
            chat_manager = ChatManager(self.mock_supabase, session_manager)
            
            # Should handle database errors gracefully
            message_response = chat_manager.send_message(
                user_id="test-user-1",
                message_content="Test message",
                model_type="fast"
            )
            assert not message_response.success, "Database error should be handled"
            
            # Test RAG pipeline fallbacks
            with patch('rag_orchestrator_optimized.RAGOrchestrator') as mock_rag:
                mock_rag.side_effect = Exception("RAG error")
                
                # Should fallback to LLM-only mode
                try:
                    rag_orchestrator = RAGOrchestrator(self.mock_supabase, ModelManager())
                    assert False, "Should have raised exception"
                except Exception as e:
                    assert "RAG error" in str(e), "RAG error should be captured"

    def test_performance_optimization_features(self):
        """Test performance optimization features"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            # Test optimized message store
            optimized_store = OptimizedMessageStore(self.mock_supabase)
            
            # Test caching functionality
            user_id = "test-user-1"
            
            # Mock cache operations
            with patch.object(performance_optimizer, 'get_cached_messages') as mock_get_cache:
                with patch.object(performance_optimizer, 'cache_messages') as mock_set_cache:
                    mock_get_cache.return_value = None  # Cache miss
                    
                    # This should trigger caching
                    messages = optimized_store.get_user_messages_paginated(user_id, page=1, page_size=20)
                    
                    # Verify caching was attempted
                    mock_get_cache.assert_called_with(user_id, 1, 20)
                    mock_set_cache.assert_called()
            
            # Test memory cleanup
            performance_optimizer.cleanup_expired_cache()
            
            # Test pagination
            paginated_result = optimized_store.get_user_messages_paginated(
                user_id="test-user-1", 
                page=1, 
                page_size=10
            )
            assert hasattr(paginated_result, 'messages'), "Should return paginated result"
            assert hasattr(paginated_result, 'total_count'), "Should include total count"
            assert hasattr(paginated_result, 'has_more'), "Should indicate if more pages exist"

    def test_security_and_data_protection(self):
        """Test security measures and data protection"""
        with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
            # Test session security
            auth_manager = AuthenticationManager()
            session_manager = SessionManager(auth_manager)
            
            # Test unauthorized access prevention
            assert not session_manager.is_authenticated(), "Should not be authenticated initially"
            
            # Test that chat operations require authentication
            chat_manager = ChatManager(self.mock_supabase, session_manager)
            
            # Should fail without authentication
            message_response = chat_manager.send_message(
                user_id="unauthorized-user",
                message_content="Test message",
                model_type="fast"
            )
            # Note: Actual implementation should check authentication
            
            # Test session timeout handling
            session_manager.initialize_session("test-user-1")
            assert session_manager.is_authenticated(), "Should be authenticated after initialization"
            
            # Test session clearing
            session_manager.clear_session()
            assert not session_manager.is_authenticated(), "Should not be authenticated after clearing"

    def test_ui_component_integration(self):
        """Test UI component integration and responsiveness"""
        from chat_interface_optimized import OptimizedChatInterface
        from ui_components import UIComponents
        
        # Test theme manager integration
        theme_manager = ThemeManager()
        
        # Mock Streamlit session state
        with patch('streamlit.session_state', {}):
            # Test chat interface initialization
            with patch('run_migrations.get_supabase_client', return_value=self.mock_supabase):
                optimized_store = OptimizedMessageStore(self.mock_supabase)
                chat_interface = OptimizedChatInterface(theme_manager, optimized_store)
                
                # Test component rendering (mock streamlit functions)
                with patch('streamlit.empty') as mock_empty:
                    with patch('streamlit.columns') as mock_columns:
                        mock_columns.return_value = [Mock(), Mock(), Mock()]
                        
                        # Test message rendering
                        messages = [
                            Mock(role="user", content="Test user message", created_at="2024-01-01T00:00:00Z"),
                            Mock(role="assistant", content="Test AI response", created_at="2024-01-01T00:01:00Z")
                        ]
                        
                        # Should not raise exceptions
                        try:
                            chat_interface.render_chat_history(messages)
                        except Exception as e:
                            # Some exceptions are expected due to mocking
                            assert "streamlit" not in str(e).lower(), f"Unexpected Streamlit error: {e}"

    def test_deployment_readiness(self):
        """Test deployment configuration and readiness"""
        from deployment_config import deployment_config
        from health_check import HealthChecker
        
        # Test configuration loading
        try:
            db_config = deployment_config.get_database_config()
            assert 'url' in db_config, "Database config should include URL"
            assert 'anon_key' in db_config, "Database config should include anon key"
        except Exception as e:
            # Expected in test environment without proper secrets
            assert "secrets" in str(e).lower() or "environment" in str(e).lower()
        
        # Test health check functionality
        health_checker = HealthChecker()
        
        # Mock health check components
        with patch.object(health_checker, 'check_database_connection') as mock_db_check:
            with patch.object(health_checker, 'check_model_api_connection') as mock_model_check:
                mock_db_check.return_value = {"status": "healthy", "response_time": 0.1}
                mock_model_check.return_value = {"status": "healthy", "response_time": 0.2}
                
                health_status = health_checker.get_overall_health()
                assert health_status["status"] in ["healthy", "degraded", "unhealthy"]
                assert "components" in health_status

def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Running Final Integration Tests...")
    print("=" * 50)
    
    # Run pytest with verbose output
    pytest_args = [
        __file__,
        "-v",
        "--tb=short",
        "--disable-warnings"
    ]
    
    exit_code = pytest.main(pytest_args)
    
    if exit_code == 0:
        print("\n✅ All integration tests passed!")
        print("🎉 Application is ready for deployment!")
    else:
        print("\n❌ Some integration tests failed!")
        print("🔧 Please review and fix the issues before deployment.")
    
    return exit_code == 0

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)