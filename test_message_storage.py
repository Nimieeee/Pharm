"""
Test script for message storage and chat management functionality.
Tests user-scoped message operations and conversation management.
"""

import os
import sys
from unittest.mock import Mock, MagicMock
from datetime import datetime
import uuid

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from message_store import MessageStore, Message
from chat_manager import ChatManager, ChatResponse, ConversationContext

def test_message_store():
    """Test MessageStore functionality with mock Supabase client"""
    print("Testing MessageStore...")
    
    # Create mock Supabase client
    mock_client = Mock()
    mock_table = Mock()
    mock_client.table.return_value = mock_table
    
    # Mock successful message save
    mock_message_data = {
        'id': str(uuid.uuid4()),
        'user_id': 'test-user-123',
        'role': 'user',
        'content': 'Test message',
        'model_used': None,
        'created_at': '2024-01-01T12:00:00Z',
        'metadata': {}
    }
    
    mock_result = Mock()
    mock_result.data = [mock_message_data]
    mock_table.insert.return_value.execute.return_value = mock_result
    
    # Test MessageStore
    message_store = MessageStore(mock_client)
    
    # Test saving a message
    message = message_store.save_message(
        user_id='test-user-123',
        role='user',
        content='Test message'
    )
    
    assert message is not None
    assert message.user_id == 'test-user-123'
    assert message.role == 'user'
    assert message.content == 'Test message'
    print("✓ Message save test passed")
    
    # Mock conversation history retrieval
    mock_history_data = [
        {
            'id': str(uuid.uuid4()),
            'user_id': 'test-user-123',
            'role': 'user',
            'content': 'Hello',
            'model_used': None,
            'created_at': '2024-01-01T12:00:00Z',
            'metadata': {}
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': 'test-user-123',
            'role': 'assistant',
            'content': 'Hi there!',
            'model_used': 'gemma2-9b-it',
            'created_at': '2024-01-01T12:01:00Z',
            'metadata': {}
        }
    ]
    
    mock_result.data = mock_history_data
    mock_table.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = mock_result
    
    # Test getting conversation history
    history = message_store.get_conversation_history('test-user-123', limit=10)
    
    assert len(history) == 2
    assert history[0].role == 'user'
    assert history[1].role == 'assistant'
    print("✓ Conversation history test passed")
    
    print("MessageStore tests completed successfully!\n")

def test_chat_manager():
    """Test ChatManager functionality with mock dependencies"""
    print("Testing ChatManager...")
    
    # Create mock Supabase client
    mock_client = Mock()
    
    # Create mock session manager
    mock_session_manager = Mock()
    mock_session_manager.is_authenticated.return_value = True
    mock_session_manager.get_user_id.return_value = 'test-user-123'
    mock_session_manager.get_model_preference.return_value = 'fast'
    
    # Create ChatManager
    chat_manager = ChatManager(mock_client, mock_session_manager)
    
    # Mock the message store
    mock_message = Message(
        id=str(uuid.uuid4()),
        user_id='test-user-123',
        role='user',
        content='Test message',
        model_used=None,
        created_at=datetime.now(),
        metadata={}
    )
    
    chat_manager.message_store.save_message = Mock(return_value=mock_message)
    chat_manager.message_store.get_conversation_history = Mock(return_value=[mock_message])
    chat_manager.message_store.get_message_count = Mock(return_value=1)
    
    # Test sending a message
    response = chat_manager.send_message('test-user-123', 'Hello, AI!')
    
    assert response.success == True
    assert response.message is not None
    assert response.message.content == 'Test message'
    print("✓ Send message test passed")
    
    # Test getting conversation history
    history = chat_manager.get_conversation_history('test-user-123')
    
    assert len(history) == 1
    assert history[0].user_id == 'test-user-123'
    print("✓ Get conversation history test passed")
    
    # Test getting conversation context
    context = chat_manager.get_conversation_context('test-user-123')
    
    assert context.user_id == 'test-user-123'
    assert len(context.messages) == 1
    assert context.model_preference == 'fast'
    assert context.total_messages == 1
    print("✓ Get conversation context test passed")
    
    # Test user access validation
    access_valid = chat_manager.validate_user_access('test-user-123')
    access_invalid = chat_manager.validate_user_access('other-user-456')
    
    assert access_valid == True
    assert access_invalid == False
    print("✓ User access validation test passed")
    
    print("ChatManager tests completed successfully!\n")

def test_user_isolation():
    """Test that user data isolation works correctly"""
    print("Testing user data isolation...")
    
    # Create mock session manager for different users
    mock_session_manager_user1 = Mock()
    mock_session_manager_user1.is_authenticated.return_value = True
    mock_session_manager_user1.get_user_id.return_value = 'user-1'
    
    mock_session_manager_user2 = Mock()
    mock_session_manager_user2.is_authenticated.return_value = True
    mock_session_manager_user2.get_user_id.return_value = 'user-2'
    
    mock_client = Mock()
    
    # Test that user 1 cannot access user 2's data
    chat_manager_user1 = ChatManager(mock_client, mock_session_manager_user1)
    
    # Try to access user 2's conversation history as user 1
    history = chat_manager_user1.get_conversation_history('user-2')
    
    # Should return empty list due to user ID mismatch
    assert len(history) == 0
    print("✓ User isolation test passed")
    
    # Test that user cannot send messages as another user
    response = chat_manager_user1.send_message('user-2', 'Unauthorized message')
    
    assert response.success == False
    assert 'mismatch' in response.error_message.lower()
    print("✓ Cross-user message prevention test passed")
    
    print("User isolation tests completed successfully!\n")

if __name__ == "__main__":
    print("Running message storage and chat management tests...\n")
    
    try:
        test_message_store()
        test_chat_manager()
        test_user_isolation()
        
        print("🎉 All tests passed successfully!")
        print("\nImplementation Summary:")
        print("- MessageStore class: ✓ Implemented with user-scoped operations")
        print("- ChatManager class: ✓ Implemented with conversation flow management")
        print("- Message persistence: ✓ Implemented with user_id association")
        print("- Conversation history: ✓ Implemented with user filtering")
        print("- User isolation: ✓ Implemented and tested")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)