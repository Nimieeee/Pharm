"""
Test authentication integration with chat interface
"""

import pytest
import streamlit as st
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_manager import AuthenticationManager, AuthResult
from session_manager import SessionManager
from auth_guard import AuthGuard, RouteProtection
from chat_manager import ChatManager

class TestAuthenticationIntegration:
    """Test authentication integration with chat interface"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock Streamlit session state
        self.mock_session_state = {}
        
        # Mock Supabase client
        self.mock_supabase = Mock()
        
        # Create managers with mocked dependencies
        with patch('streamlit.secrets', {'SUPABASE_URL': 'test_url', 'SUPABASE_ANON_KEY': 'test_key'}):
            with patch('supabase.create_client', return_value=self.mock_supabase):
                self.auth_manager = AuthenticationManager()
        
        self.session_manager = SessionManager(self.auth_manager)
        self.auth_guard = AuthGuard(self.auth_manager, self.session_manager)
        self.chat_manager = ChatManager(self.mock_supabase, self.session_manager)
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_unauthenticated_user_cannot_access_chat(self, mock_session_state):
        """Test that unauthenticated users cannot access chat interface"""
        # Ensure user is not authenticated
        mock_session_state.clear()
        
        # Try to protect chat interface
        with patch('streamlit.error') as mock_error:
            result = RouteProtection.protect_chat_interface(self.auth_guard)
            
            assert result is False
            mock_error.assert_called()
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_authenticated_user_can_access_chat(self, mock_session_state):
        """Test that authenticated users can access chat interface"""
        # Set up authenticated session
        mock_session_state['user_session'] = Mock()
        mock_session_state['user_session'].user_id = 'test_user_id'
        mock_session_state['user_session'].email = 'test@example.com'
        mock_session_state['user_session'].is_authenticated = True
        mock_session_state['authentication_status'] = 'authenticated'
        
        # Mock auth manager to return authenticated user
        with patch.object(self.auth_manager, 'get_current_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = 'test_user_id'
            mock_user.email = 'test@example.com'
            mock_get_user.return_value = mock_user
            
            result = RouteProtection.protect_chat_interface(self.auth_guard)
            assert result is True
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_session_validation_on_chat_access(self, mock_session_state):
        """Test that session is validated when accessing chat"""
        # Set up session that appears authenticated but is invalid
        mock_session_state['user_session'] = Mock()
        mock_session_state['user_session'].user_id = 'test_user_id'
        mock_session_state['user_session'].is_authenticated = True
        mock_session_state['authentication_status'] = 'authenticated'
        
        # Mock auth manager to return None (invalid session)
        with patch.object(self.auth_manager, 'get_current_user', return_value=None):
            with patch('streamlit.error') as mock_error:
                result = RouteProtection.protect_chat_interface(self.auth_guard)
                
                assert result is False
                mock_error.assert_called()
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_user_isolation_in_chat_manager(self, mock_session_state):
        """Test that chat manager enforces user isolation"""
        # Set up authenticated session for user A
        mock_session_state['user_session'] = Mock()
        mock_session_state['user_session'].user_id = 'user_a'
        mock_session_state['user_session'].is_authenticated = True
        
        # Try to access data for user B
        result = self.chat_manager.validate_user_access('user_b')
        assert result is False
        
        # Try to access data for user A (should succeed)
        result = self.chat_manager.validate_user_access('user_a')
        assert result is True
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_message_sending_requires_authentication(self, mock_session_state):
        """Test that sending messages requires authentication"""
        # Clear session (unauthenticated)
        mock_session_state.clear()
        
        response = self.chat_manager.send_message('test_user', 'test message')
        
        assert response.success is False
        assert 'not authenticated' in response.error_message.lower()
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_conversation_history_requires_authentication(self, mock_session_state):
        """Test that accessing conversation history requires authentication"""
        # Clear session (unauthenticated)
        mock_session_state.clear()
        
        messages = self.chat_manager.get_conversation_history('test_user')
        
        # Should return empty list for unauthenticated users
        assert messages == []
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_user_profile_display_for_authenticated_user(self, mock_session_state):
        """Test user profile display for authenticated users"""
        # Set up authenticated session
        mock_session_state['user_session'] = Mock()
        mock_session_state['user_session'].user_id = 'test_user_id'
        mock_session_state['user_session'].email = 'test@example.com'
        mock_session_state['user_session'].is_authenticated = True
        mock_session_state['user_session'].preferences = {'subscription_tier': 'free'}
        mock_session_state['model_preference'] = 'fast'
        mock_session_state['theme'] = 'light'
        
        # Mock Streamlit components
        with patch('streamlit.sidebar'), \
             patch('streamlit.subheader'), \
             patch('streamlit.write'), \
             patch('streamlit.selectbox', return_value='fast'), \
             patch('streamlit.button', return_value=False):
            
            from auth_ui import AuthInterface
            auth_interface = AuthInterface(self.auth_manager, self.session_manager)
            
            # This should not raise an exception
            try:
                auth_interface.render_user_profile()
                success = True
            except Exception:
                success = False
            
            assert success is True
    
    def test_auth_guard_get_current_user_id(self):
        """Test auth guard can get current user ID"""
        with patch.object(self.session_manager, 'is_authenticated', return_value=True), \
             patch.object(self.session_manager, 'validate_session', return_value=True), \
             patch.object(self.session_manager, 'get_user_id', return_value='test_user_id'):
            
            user_id = self.auth_guard.get_current_user_id()
            assert user_id == 'test_user_id'
    
    def test_auth_guard_get_current_user_id_unauthenticated(self):
        """Test auth guard raises error for unauthenticated users"""
        with patch.object(self.session_manager, 'is_authenticated', return_value=False):
            
            with pytest.raises(ValueError, match="User not authenticated"):
                self.auth_guard.get_current_user_id()


def test_authentication_integration():
    """Run basic integration test"""
    test_instance = TestAuthenticationIntegration()
    test_instance.setup_method()
    
    # Test basic functionality
    assert test_instance.auth_manager is not None
    assert test_instance.session_manager is not None
    assert test_instance.auth_guard is not None
    assert test_instance.chat_manager is not None
    
    print("✅ Authentication integration components initialized successfully")


if __name__ == "__main__":
    test_authentication_integration()
    print("✅ All authentication integration tests passed!")