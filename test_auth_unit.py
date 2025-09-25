"""
Unit tests for authentication manager and session handling
Comprehensive testing of auth components with mocked dependencies
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
from datetime import datetime
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_manager import AuthenticationManager, AuthResult, User
from session_manager import SessionManager, UserSession
from auth_guard import AuthGuard, RouteProtection


class TestAuthenticationManager(unittest.TestCase):
    """Unit tests for AuthenticationManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_secrets = {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_ANON_KEY': 'test_anon_key'
        }
        
        self.mock_supabase_client = Mock()
        self.mock_supabase_client.auth.get_session.return_value = None
    
    @patch('streamlit.secrets')
    @patch('supabase.create_client')
    def test_initialization_success(self, mock_create_client, mock_secrets):
        """Test successful initialization of AuthenticationManager"""
        mock_secrets.__getitem__.side_effect = self.mock_secrets.__getitem__
        mock_create_client.return_value = self.mock_supabase_client
        
        auth_manager = AuthenticationManager()
        
        self.assertIsNotNone(auth_manager)
        self.assertEqual(auth_manager.supabase_url, 'https://test.supabase.co')
        self.assertEqual(auth_manager.supabase_key, 'test_anon_key')
        mock_create_client.assert_called_once()
    
    @patch('streamlit.secrets')
    @patch('streamlit.error')
    @patch('streamlit.stop')
    def test_initialization_missing_secrets(self, mock_stop, mock_error, mock_secrets):
        """Test initialization failure with missing secrets"""
        mock_secrets.__getitem__.side_effect = KeyError('SUPABASE_URL')
        
        with self.assertRaises(SystemExit):
            AuthenticationManager()
        
        mock_error.assert_called()
        mock_stop.assert_called()
    
    @patch('streamlit.secrets')
    @patch('supabase.create_client')
    def test_sign_up_validation_empty_fields(self, mock_create_client, mock_secrets):
        """Test sign up validation with empty fields"""
        mock_secrets.__getitem__.side_effect = self.mock_secrets.__getitem__
        mock_create_client.return_value = self.mock_supabase_client
        
        auth_manager = AuthenticationManager()
        
        # Test empty email
        result = auth_manager.sign_up("", "password123")
        self.assertFalse(result.success)
        self.assertIn("required", result.error_message.lower())
        
        # Test empty password
        result = auth_manager.sign_up("test@example.com", "")
        self.assertFalse(result.success)
        self.assertIn("required", result.error_message.lower())
    
    @patch('streamlit.secrets')
    @patch('supabase.create_client')
    def test_sign_up_validation_short_password(self, mock_create_client, mock_secrets):
        """Test sign up validation with short password"""
        mock_secrets.__getitem__.side_effect = self.mock_secrets.__getitem__
        mock_create_client.return_value = self.mock_supabase_client
        
        auth_manager = AuthenticationManager()
        
        result = auth_manager.sign_up("test@example.com", "123")
        self.assertFalse(result.success)
        self.assertIn("6 characters", result.error_message)
    
    @patch('streamlit.secrets')
    @patch('supabase.create_client')
    def test_sign_up_success(self, mock_create_client, mock_secrets):
        """Test successful sign up"""
        mock_secrets.__getitem__.side_effect = self.mock_secrets.__getitem__
        mock_create_client.return_value = self.mock_supabase_client
        
        # Mock successful sign up response
        mock_user = Mock()
        mock_user.id = 'user123'
        mock_user.email = 'test@example.com'
        mock_user.user_metadata = {'name': 'Test User'}
        
        mock_response = Mock()
        mock_response.user = mock_user
        
        self.mock_supabase_client.auth.sign_up.return_value = mock_response
        
        auth_manager = AuthenticationManager()
        result = auth_manager.sign_up("test@example.com", "password123")
        
        self.assertTrue(result.success)
        self.assertEqual(result.user_id, 'user123')
        self.assertEqual(result.email, 'test@example.com')
        self.assertIsNotNone(result.user_data)
    
    @patch('streamlit.secrets')
    @patch('supabase.create_client')
    def test_sign_in_validation(self, mock_create_client, mock_secrets):
        """Test sign in validation"""
        mock_secrets.__getitem__.side_effect = self.mock_secrets.__getitem__
        mock_create_client.return_value = self.mock_supabase_client
        
        auth_manager = AuthenticationManager()
        
        # Test empty credentials
        result = auth_manager.sign_in("", "")
        self.assertFalse(result.success)
        self.assertIn("required", result.error_message.lower())
    
    @patch('streamlit.secrets')
    @patch('supabase.create_client')
    def test_sign_in_success(self, mock_create_client, mock_secrets):
        """Test successful sign in"""
        mock_secrets.__getitem__.side_effect = self.mock_secrets.__getitem__
        mock_create_client.return_value = self.mock_supabase_client
        
        # Mock successful sign in response
        mock_user = Mock()
        mock_user.id = 'user123'
        mock_user.email = 'test@example.com'
        mock_user.user_metadata = {}
        
        mock_response = Mock()
        mock_response.user = mock_user
        
        self.mock_supabase_client.auth.sign_in_with_password.return_value = mock_response
        
        auth_manager = AuthenticationManager()
        result = auth_manager.sign_in("test@example.com", "password123")
        
        self.assertTrue(result.success)
        self.assertEqual(result.user_id, 'user123')
        self.assertEqual(result.email, 'test@example.com')
    
    @patch('streamlit.secrets')
    @patch('supabase.create_client')
    def test_sign_out(self, mock_create_client, mock_secrets):
        """Test sign out functionality"""
        mock_secrets.__getitem__.side_effect = self.mock_secrets.__getitem__
        mock_create_client.return_value = self.mock_supabase_client
        
        auth_manager = AuthenticationManager()
        result = auth_manager.sign_out()
        
        self.assertTrue(result)
        self.mock_supabase_client.auth.sign_out.assert_called_once()
    
    @patch('streamlit.secrets')
    @patch('supabase.create_client')
    def test_get_current_user_authenticated(self, mock_create_client, mock_secrets):
        """Test getting current user when authenticated"""
        mock_secrets.__getitem__.side_effect = self.mock_secrets.__getitem__
        mock_create_client.return_value = self.mock_supabase_client
        
        # Mock authenticated user
        mock_user_data = Mock()
        mock_user_data.id = 'user123'
        mock_user_data.email = 'test@example.com'
        mock_user_data.created_at = '2024-01-01T00:00:00Z'
        mock_user_data.user_metadata = {'theme': 'light'}
        
        mock_user_response = Mock()
        mock_user_response.user = mock_user_data
        
        self.mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        auth_manager = AuthenticationManager()
        user = auth_manager.get_current_user()
        
        self.assertIsNotNone(user)
        self.assertIsInstance(user, User)
        self.assertEqual(user.id, 'user123')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.subscription_tier, 'free')
    
    @patch('streamlit.secrets')
    @patch('supabase.create_client')
    def test_get_current_user_not_authenticated(self, mock_create_client, mock_secrets):
        """Test getting current user when not authenticated"""
        mock_secrets.__getitem__.side_effect = self.mock_secrets.__getitem__
        mock_create_client.return_value = self.mock_supabase_client
        
        # Mock no user
        mock_user_response = Mock()
        mock_user_response.user = None
        
        self.mock_supabase_client.auth.get_user.return_value = mock_user_response
        
        auth_manager = AuthenticationManager()
        user = auth_manager.get_current_user()
        
        self.assertIsNone(user)
    
    @patch('streamlit.secrets')
    @patch('supabase.create_client')
    def test_is_authenticated(self, mock_create_client, mock_secrets):
        """Test authentication status check"""
        mock_secrets.__getitem__.side_effect = self.mock_secrets.__getitem__
        mock_create_client.return_value = self.mock_supabase_client
        
        auth_manager = AuthenticationManager()
        
        # Mock authenticated user
        with patch.object(auth_manager, 'get_current_user', return_value=Mock()):
            self.assertTrue(auth_manager.is_authenticated())
        
        # Mock no user
        with patch.object(auth_manager, 'get_current_user', return_value=None):
            self.assertFalse(auth_manager.is_authenticated())


class TestSessionManager(unittest.TestCase):
    """Unit tests for SessionManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_auth_manager = Mock()
        self.mock_session_state = {}
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_initialization(self, mock_session_state):
        """Test SessionManager initialization"""
        session_manager = SessionManager(self.mock_auth_manager)
        
        self.assertEqual(session_manager.auth_manager, self.mock_auth_manager)
        self.assertIn('user_session', mock_session_state)
        self.assertIn('authentication_status', mock_session_state)
        self.assertIn('model_preference', mock_session_state)
        self.assertIn('theme', mock_session_state)
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_initialize_session(self, mock_session_state):
        """Test session initialization"""
        session_manager = SessionManager(self.mock_auth_manager)
        
        preferences = {'theme': 'dark', 'model_preference': 'premium'}
        session_manager.initialize_session('user123', 'test@example.com', preferences)
        
        self.assertIsNotNone(mock_session_state['user_session'])
        self.assertEqual(mock_session_state['user_session'].user_id, 'user123')
        self.assertEqual(mock_session_state['user_session'].email, 'test@example.com')
        self.assertEqual(mock_session_state['authentication_status'], 'authenticated')
        self.assertEqual(mock_session_state['theme'], 'dark')
        self.assertEqual(mock_session_state['model_preference'], 'premium')
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_get_user_session(self, mock_session_state):
        """Test getting user session"""
        session_manager = SessionManager(self.mock_auth_manager)
        
        # Test with no session
        result = session_manager.get_user_session()
        self.assertIsNone(result)
        
        # Test with session
        session_manager.initialize_session('user123', 'test@example.com')
        result = session_manager.get_user_session()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, UserSession)
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_clear_session(self, mock_session_state):
        """Test session clearing"""
        session_manager = SessionManager(self.mock_auth_manager)
        
        # Initialize session first
        session_manager.initialize_session('user123', 'test@example.com')
        self.assertIsNotNone(mock_session_state['user_session'])
        
        # Clear session
        session_manager.clear_session()
        self.assertIsNone(mock_session_state['user_session'])
        self.assertIsNone(mock_session_state['authentication_status'])
        self.assertEqual(mock_session_state['model_preference'], 'fast')
        self.assertEqual(mock_session_state['theme'], 'light')
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_is_authenticated(self, mock_session_state):
        """Test authentication status check"""
        session_manager = SessionManager(self.mock_auth_manager)
        
        # Test not authenticated
        self.assertFalse(session_manager.is_authenticated())
        
        # Test authenticated
        session_manager.initialize_session('user123', 'test@example.com')
        self.assertTrue(session_manager.is_authenticated())
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_get_user_id(self, mock_session_state):
        """Test getting user ID"""
        session_manager = SessionManager(self.mock_auth_manager)
        
        # Test with no session
        self.assertIsNone(session_manager.get_user_id())
        
        # Test with session
        session_manager.initialize_session('user123', 'test@example.com')
        self.assertEqual(session_manager.get_user_id(), 'user123')
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_update_preferences(self, mock_session_state):
        """Test updating user preferences"""
        session_manager = SessionManager(self.mock_auth_manager)
        session_manager.initialize_session('user123', 'test@example.com')
        
        # Test model preference update
        session_manager.update_model_preference('premium')
        self.assertEqual(mock_session_state['model_preference'], 'premium')
        self.assertEqual(mock_session_state['user_session'].model_preference, 'premium')
        
        # Test theme update
        session_manager.update_theme('dark')
        self.assertEqual(mock_session_state['theme'], 'dark')
        self.assertEqual(mock_session_state['user_session'].theme, 'dark')
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_validate_session(self, mock_session_state):
        """Test session validation"""
        session_manager = SessionManager(self.mock_auth_manager)
        
        # Test with no session
        self.assertFalse(session_manager.validate_session())
        
        # Test with valid session
        session_manager.initialize_session('user123', 'test@example.com')
        self.mock_auth_manager.get_current_user.return_value = Mock(id='user123')
        self.assertTrue(session_manager.validate_session())
        
        # Test with invalid session
        self.mock_auth_manager.get_current_user.return_value = None
        self.assertFalse(session_manager.validate_session())
        self.assertIsNone(mock_session_state['user_session'])


class TestAuthGuard(unittest.TestCase):
    """Unit tests for AuthGuard class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_auth_manager = Mock()
        self.mock_session_manager = Mock()
        self.auth_guard = AuthGuard(self.mock_auth_manager, self.mock_session_manager)
    
    def test_initialization(self):
        """Test AuthGuard initialization"""
        self.assertEqual(self.auth_guard.auth_manager, self.mock_auth_manager)
        self.assertEqual(self.auth_guard.session_manager, self.mock_session_manager)
    
    def test_get_current_user_id_authenticated(self):
        """Test getting current user ID when authenticated"""
        self.mock_session_manager.is_authenticated.return_value = True
        self.mock_session_manager.validate_session.return_value = True
        self.mock_session_manager.get_user_id.return_value = 'user123'
        
        user_id = self.auth_guard.get_current_user_id()
        self.assertEqual(user_id, 'user123')
    
    def test_get_current_user_id_not_authenticated(self):
        """Test getting current user ID when not authenticated"""
        self.mock_session_manager.is_authenticated.return_value = False
        
        with self.assertRaises(ValueError) as context:
            self.auth_guard.get_current_user_id()
        
        self.assertIn("not authenticated", str(context.exception).lower())
    
    def test_require_authentication_success(self):
        """Test successful authentication requirement"""
        self.mock_session_manager.is_authenticated.return_value = True
        self.mock_session_manager.validate_session.return_value = True
        
        result = self.auth_guard.require_authentication()
        self.assertTrue(result)
    
    def test_require_authentication_failure(self):
        """Test failed authentication requirement"""
        self.mock_session_manager.is_authenticated.return_value = False
        
        with patch('streamlit.error') as mock_error:
            result = self.auth_guard.require_authentication()
            self.assertFalse(result)
            mock_error.assert_called()


class TestRouteProtection(unittest.TestCase):
    """Unit tests for RouteProtection class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_auth_guard = Mock()
    
    @patch('streamlit.error')
    def test_protect_chat_interface_authenticated(self, mock_error):
        """Test chat interface protection for authenticated user"""
        self.mock_auth_guard.require_authentication.return_value = True
        
        result = RouteProtection.protect_chat_interface(self.mock_auth_guard)
        self.assertTrue(result)
        mock_error.assert_not_called()
    
    @patch('streamlit.error')
    def test_protect_chat_interface_not_authenticated(self, mock_error):
        """Test chat interface protection for unauthenticated user"""
        self.mock_auth_guard.require_authentication.return_value = False
        
        result = RouteProtection.protect_chat_interface(self.mock_auth_guard)
        self.assertFalse(result)
        mock_error.assert_called()


def run_auth_unit_tests():
    """Run all authentication unit tests"""
    print("🔐 Running Authentication Unit Tests")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestAuthenticationManager,
        TestSessionManager,
        TestAuthGuard,
        TestRouteProtection
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All authentication unit tests passed!")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False


if __name__ == "__main__":
    success = run_auth_unit_tests()
    exit(0 if success else 1)