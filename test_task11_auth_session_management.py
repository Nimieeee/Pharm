#!/usr/bin/env python3
"""
Test Task 11: Update authentication and session management
Tests the implementation of simplified user profile, conversation switching, and user isolation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock streamlit before importing our modules
sys.modules['streamlit'] = Mock()
import streamlit as st

# Create a proper mock session state that behaves like a dictionary with attribute access
class MockSessionState(dict):
    def __getattr__(self, key):
        return self.get(key)
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def __delattr__(self, key):
        if key in self:
            del self[key]

# Mock session state
st.session_state = MockSessionState()

from auth_manager import AuthenticationManager, User
from session_manager import SessionManager, UserSession
from auth_ui import AuthInterface
from conversation_ui import ConversationUI
from conversation_manager import ConversationManager, Conversation
from theme_manager import ThemeManager
from datetime import datetime

class TestTask11AuthSessionManagement(unittest.TestCase):
    """Test authentication and session management updates"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset session state
        st.session_state.clear()
        
        # Mock dependencies
        self.mock_auth_manager = Mock(spec=AuthenticationManager)
        self.mock_supabase_client = Mock()
        self.mock_theme_manager = Mock(spec=ThemeManager)
        
        # Create session manager
        self.session_manager = SessionManager(self.mock_auth_manager)
        
        # Create auth interface
        self.auth_interface = AuthInterface(self.mock_auth_manager, self.session_manager)
        
        # Create conversation manager and UI
        self.conversation_manager = Mock(spec=ConversationManager)
        self.conversation_ui = ConversationUI(self.conversation_manager, self.mock_theme_manager, self.session_manager)
    
    def test_session_state_initialization(self):
        """Test that session state is properly initialized with conversation management"""
        # Session state should be initialized with conversation management variables
        expected_keys = [
            'user_session', 'authentication_status', 'user_preferences',
            'model_preference', 'theme', 'conversation_history',
            'current_conversation_id', 'user_conversations', 
            'conversation_switched', 'conversation_isolation_user_id'
        ]
        
        for key in expected_keys:
            self.assertIn(key, st.session_state)
    
    def test_user_profile_no_plan_information(self):
        """Test that user profile doesn't display plan/subscription information"""
        # Create a mock user session
        user_session = UserSession(
            user_id="test_user_123",
            email="test@example.com",
            preferences={"subscription_tier": "premium"},  # This should not be displayed
            model_preference="fast",
            theme="dark",
            is_authenticated=True
        )
        
        st.session_state.user_session = user_session
        st.session_state.model_preference = "fast"
        
        # Mock streamlit components
        with patch('streamlit.sidebar'), \
             patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.write') as mock_write, \
             patch('streamlit.checkbox') as mock_checkbox, \
             patch('streamlit.button') as mock_button:
            
            mock_checkbox.return_value = False
            mock_button.return_value = False
            
            # Render user profile
            self.auth_interface.render_user_profile()
            
            # Check that email is displayed
            mock_write.assert_called()
            write_calls = [call[0][0] for call in mock_write.call_args_list]
            email_displayed = any("test@example.com" in str(call) for call in write_calls)
            self.assertTrue(email_displayed, "User email should be displayed")
            
            # Check that no plan/subscription information is displayed
            all_calls = []
            for call in mock_markdown.call_args_list:
                all_calls.extend(call[0])
            for call in mock_write.call_args_list:
                all_calls.extend(call[0])
            
            all_text = " ".join(str(call) for call in all_calls)
            
            # These terms should NOT appear in the user profile
            forbidden_terms = ["subscription", "plan", "tier", "free", "premium plan", "subscription tier"]
            for term in forbidden_terms:
                self.assertNotIn(term.lower(), all_text.lower(), 
                               f"Plan information '{term}' should not be displayed in user profile")
    
    def test_conversation_switching_with_isolation(self):
        """Test conversation switching with proper user isolation"""
        user_id = "test_user_123"
        conversation_id = "conv_456"
        
        # Mock authentication
        self.session_manager.is_authenticated = Mock(return_value=True)
        self.session_manager.get_user_id = Mock(return_value=user_id)
        
        # Mock conversation ownership verification
        self.session_manager._verify_conversation_ownership = Mock(return_value=True)
        
        # Test conversation switching
        result = self.session_manager.switch_conversation(conversation_id)
        
        self.assertTrue(result, "Conversation switch should succeed")
        self.assertEqual(st.session_state.current_conversation_id, conversation_id)
        self.assertEqual(st.session_state.conversation_isolation_user_id, user_id)
        self.assertTrue(st.session_state.conversation_switched)
        self.assertEqual(st.session_state.conversation_history, [])  # Should be cleared
    
    def test_conversation_isolation_between_users(self):
        """Test that conversations are properly isolated between different users"""
        user1_id = "user_123"
        user2_id = "user_456"
        conversation_id = "conv_789"
        
        # Set up initial state for user1
        st.session_state.current_conversation_id = conversation_id
        st.session_state.conversation_isolation_user_id = user1_id
        st.session_state.user_conversations = ["conv1", "conv2"]
        
        # Mock authentication for user2
        self.session_manager.is_authenticated = Mock(return_value=True)
        self.session_manager.get_user_id = Mock(return_value=user2_id)
        
        # When user2 tries to get current conversation, it should be cleared
        current_conv = self.session_manager.get_current_conversation_id()
        
        self.assertIsNone(current_conv, "Conversation should be cleared when user changes")
        self.assertEqual(st.session_state.conversation_isolation_user_id, user2_id)
        self.assertIsNone(st.session_state.current_conversation_id)
        
        # User conversations should also be cleared
        user_conversations = self.session_manager.get_user_conversations()
        self.assertEqual(user_conversations, [], "User conversations should be cleared when user changes")
    
    def test_conversation_ownership_verification(self):
        """Test conversation ownership verification"""
        user_id = "test_user_123"
        conversation_id = "conv_456"
        
        # Mock database response for ownership verification
        mock_result = Mock()
        mock_result.data = [{"user_id": user_id}]  # Conversation belongs to user
        
        self.mock_auth_manager.supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.execute.return_value = mock_result
        
        # Test ownership verification
        result = self.session_manager._verify_conversation_ownership(user_id, conversation_id)
        
        self.assertTrue(result, "Conversation ownership should be verified")
        
        # Test with wrong user
        mock_result.data = []  # No matching records
        result = self.session_manager._verify_conversation_ownership("wrong_user", conversation_id)
        
        self.assertFalse(result, "Conversation ownership should be denied for wrong user")
    
    def test_session_clear_removes_conversation_data(self):
        """Test that clearing session removes all conversation-related data"""
        # Set up session with conversation data
        st.session_state.current_conversation_id = "conv_123"
        st.session_state.user_conversations = ["conv1", "conv2"]
        st.session_state.conversation_switched = True
        st.session_state.conversation_isolation_user_id = "user_123"
        st.session_state.conversation_custom_data = "test"
        
        # Clear session
        self.session_manager.clear_session()
        
        # Verify conversation data is cleared
        self.assertIsNone(st.session_state.current_conversation_id)
        self.assertEqual(st.session_state.user_conversations, [])
        self.assertFalse(st.session_state.conversation_switched)
        self.assertIsNone(st.session_state.conversation_isolation_user_id)
        self.assertNotIn('conversation_custom_data', st.session_state)
    
    def test_initialize_session_sets_conversation_isolation(self):
        """Test that session initialization sets up conversation isolation"""
        user_id = "test_user_123"
        email = "test@example.com"
        
        # Mock user existence check
        self.session_manager._ensure_user_exists = Mock(return_value=True)
        self.session_manager.load_user_preferences = Mock(return_value={})
        
        # Initialize session
        self.session_manager.initialize_session(user_id, email)
        
        # Verify conversation isolation is set up
        self.assertEqual(st.session_state.conversation_isolation_user_id, user_id)
        self.assertIsNone(st.session_state.current_conversation_id)
        self.assertEqual(st.session_state.user_conversations, [])
        self.assertFalse(st.session_state.conversation_switched)
    
    def test_conversation_ui_uses_session_manager(self):
        """Test that conversation UI properly uses session manager for switching"""
        user_id = "test_user_123"
        conversations = [
            Conversation(
                id="conv1",
                user_id=user_id,
                title="Test Conversation 1",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                message_count=5,
                is_active=True
            ),
            Conversation(
                id="conv2",
                user_id=user_id,
                title="Test Conversation 2",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                message_count=3,
                is_active=True
            )
        ]
        
        # Mock conversation manager
        self.conversation_manager.get_user_conversations.return_value = conversations
        self.conversation_manager.get_or_create_default_conversation.return_value = conversations[0]
        
        # Mock session manager methods
        self.session_manager.get_current_conversation_id = Mock(return_value=None)
        self.session_manager.set_current_conversation_id = Mock(return_value=True)
        self.session_manager.switch_conversation = Mock(return_value=True)
        
        # Test rendering conversation tabs
        with patch('streamlit.tabs') as mock_tabs:
            mock_tabs.return_value = [Mock(), Mock(), Mock()]  # 2 conversations + new tab
            
            result = self.conversation_ui.render_conversation_tabs(user_id)
            
            # Verify session manager was used
            self.session_manager.get_current_conversation_id.assert_called()
            self.session_manager.set_current_conversation_id.assert_called_with(conversations[0].id)
    
    def test_unauthorized_conversation_access_blocked(self):
        """Test that unauthorized users cannot access conversations"""
        # Mock unauthenticated state
        self.session_manager.is_authenticated = Mock(return_value=False)
        
        # Try to switch conversation
        result = self.session_manager.switch_conversation("conv_123")
        self.assertFalse(result, "Unauthenticated users should not be able to switch conversations")
        
        # Try to get current conversation
        current_conv = self.session_manager.get_current_conversation_id()
        self.assertIsNone(current_conv, "Unauthenticated users should not get conversation ID")
        
        # Try to set conversation
        result = self.session_manager.set_current_conversation_id("conv_123")
        self.assertFalse(result, "Unauthenticated users should not be able to set conversation ID")

def run_tests():
    """Run the test suite"""
    print("🧪 Running Task 11 Authentication and Session Management Tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTask11AuthSessionManagement)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ All tests passed! Task 11 implementation is working correctly.")
        print("\n🎯 Task 11 Requirements Verified:")
        print("   ✅ User profile display removes plan information")
        print("   ✅ Session management handles conversation switching")
        print("   ✅ Conversation isolation between different users")
        print("   ✅ Conversation management added to user session state")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for test, error in result.failures + result.errors:
            print(f"   ❌ {test}: {error.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)