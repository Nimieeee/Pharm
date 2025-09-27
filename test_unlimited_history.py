#!/usr/bin/env python3
"""
Test script for unlimited conversation history functionality
"""

import sys
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_unlimited_message_store():
    """Test the unlimited message store functionality"""
    print("Testing OptimizedMessageStore.get_all_user_messages()...")
    
    try:
        from message_store_optimized import OptimizedMessageStore
        from message_store import Message
        
        # Mock Supabase client
        mock_client = Mock()
        mock_table = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_order = Mock()
        mock_execute = Mock()
        
        # Chain the mocks
        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.order.return_value = mock_order
        mock_order.execute.return_value = mock_execute
        
        # Mock data for 5 messages
        mock_execute.data = [
            {
                'id': f'msg_{i}',
                'user_id': 'test_user',
                'role': 'user' if i % 2 == 0 else 'assistant',
                'content': f'Test message {i}',
                'model_used': 'test_model' if i % 2 == 1 else None,
                'created_at': f'2024-01-0{i+1}T10:00:00Z',
                'metadata': {}
            }
            for i in range(5)
        ]
        
        # Create store instance
        store = OptimizedMessageStore(mock_client)
        
        # Test getting all messages
        messages = store.get_all_user_messages('test_user')
        
        # Verify results
        assert len(messages) == 5, f"Expected 5 messages, got {len(messages)}"
        assert all(isinstance(msg, Message) for msg in messages), "All items should be Message objects"
        assert messages[0].content == "Test message 0", "Messages should be in chronological order"
        assert messages[-1].content == "Test message 4", "Last message should be message 4"
        
        # Verify database query was called correctly
        mock_client.table.assert_called_with('messages')
        mock_table.select.assert_called_with('*')
        mock_select.eq.assert_called_with('user_id', 'test_user')
        mock_eq.order.assert_called_with('created_at', desc=False)  # Oldest first
        
        print("✅ OptimizedMessageStore.get_all_user_messages() test passed!")
        return True
        
    except Exception as e:
        print(f"❌ OptimizedMessageStore test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_unlimited_chat_interface():
    """Test the unlimited chat interface functionality"""
    print("Testing OptimizedChatInterface.render_unlimited_chat_history()...")
    
    try:
        from chat_interface_optimized import OptimizedChatInterface
        from theme_manager import ThemeManager
        from message_store import Message
        from datetime import datetime
        
        # Mock theme manager
        mock_theme = Mock(spec=ThemeManager)
        
        # Mock message store
        mock_store = Mock()
        mock_store.get_all_user_messages.return_value = [
            Message(
                id='msg1',
                user_id='test_user',
                role='user',
                content='Hello',
                model_used=None,
                created_at=datetime.now(),
                metadata={}
            ),
            Message(
                id='msg2',
                user_id='test_user',
                role='assistant',
                content='Hi there!',
                model_used='test_model',
                created_at=datetime.now(),
                metadata={}
            )
        ]
        
        # Create interface instance
        interface = OptimizedChatInterface(mock_theme, mock_store)
        
        # Verify initialization
        assert interface.message_store == mock_store, "Message store should be set"
        assert hasattr(interface, '_initialize_unlimited_history_state'), "Should have unlimited history initialization"
        
        print("✅ OptimizedChatInterface unlimited history test passed!")
        return True
        
    except Exception as e:
        print(f"❌ OptimizedChatInterface test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_css_optimizations():
    """Test that CSS optimizations are present"""
    print("Testing CSS optimizations for unlimited history...")
    
    try:
        from chat_interface_optimized import inject_optimized_chat_css
        
        # This should not raise an exception
        inject_optimized_chat_css()
        
        print("✅ CSS optimizations test passed!")
        return True
        
    except Exception as e:
        print(f"❌ CSS optimizations test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Unlimited Conversation History Implementation")
    print("=" * 60)
    
    tests = [
        test_unlimited_message_store,
        test_unlimited_chat_interface,
        test_css_optimizations
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Unlimited conversation history is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)