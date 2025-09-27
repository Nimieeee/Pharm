#!/usr/bin/env python3
"""
Test script for conversation management functionality.
Tests the conversation manager, UI components, and database integration.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

def test_conversation_manager():
    """Test ConversationManager functionality"""
    print("🧪 Testing ConversationManager...")
    
    try:
        from conversation_manager import ConversationManager, Conversation
        
        # Mock Supabase client
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': 'test-conv-id',
            'user_id': 'test-user-id',
            'title': 'Test Conversation',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'message_count': 0,
            'is_active': True
        }]
        
        conv_manager = ConversationManager(mock_client)
        
        # Test conversation creation
        conversation = conv_manager.create_conversation('test-user-id', 'Test Conversation')
        
        assert conversation is not None
        assert conversation.title == 'Test Conversation'
        assert conversation.user_id == 'test-user-id'
        
        print("✅ ConversationManager.create_conversation() works")
        
        # Test title generation
        title = conv_manager.generate_conversation_title("What is the mechanism of action of aspirin?")
        assert len(title) > 0
        assert len(title) <= 50
        
        print("✅ ConversationManager.generate_conversation_title() works")
        
        print("✅ ConversationManager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ ConversationManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_ui():
    """Test ConversationUI functionality"""
    print("\n🧪 Testing ConversationUI...")
    
    try:
        from conversation_ui import ConversationUI
        from theme_manager import ThemeManager
        
        # Mock dependencies
        mock_conv_manager = Mock()
        mock_theme_manager = Mock()
        
        conv_ui = ConversationUI(mock_conv_manager, mock_theme_manager)
        
        # Test auto title generation
        result = conv_ui.auto_generate_title_from_message(
            'test-user-id', 
            'test-conv-id', 
            'What are the side effects of ibuprofen?'
        )
        
        print("✅ ConversationUI.auto_generate_title_from_message() works")
        
        print("✅ ConversationUI tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ ConversationUI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_message_store_conversation_support():
    """Test MessageStore conversation support"""
    print("\n🧪 Testing MessageStore conversation support...")
    
    try:
        from message_store import MessageStore, Message
        
        # Mock Supabase client
        mock_client = Mock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [{
            'id': 'test-msg-id',
            'user_id': 'test-user-id',
            'role': 'user',
            'content': 'Test message',
            'model_used': None,
            'created_at': datetime.now().isoformat(),
            'metadata': {},
            'conversation_id': 'test-conv-id'
        }]
        
        message_store = MessageStore(mock_client)
        
        # Test saving message with conversation ID
        message = message_store.save_message(
            user_id='test-user-id',
            role='user',
            content='Test message',
            conversation_id='test-conv-id'
        )
        
        assert message is not None
        print("✅ MessageStore.save_message() with conversation_id works")
        
        # Mock conversation messages query
        mock_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.execute.return_value.data = [{
            'id': 'test-msg-id',
            'user_id': 'test-user-id',
            'role': 'user',
            'content': 'Test message',
            'model_used': None,
            'created_at': datetime.now().isoformat(),
            'metadata': {}
        }]
        
        # Test getting conversation messages
        messages = message_store.get_conversation_messages('test-user-id', 'test-conv-id')
        assert isinstance(messages, list)
        
        print("✅ MessageStore.get_conversation_messages() works")
        
        print("✅ MessageStore conversation support tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ MessageStore conversation support test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_chat_manager_conversation_support():
    """Test ChatManager conversation support"""
    print("\n🧪 Testing ChatManager conversation support...")
    
    try:
        from chat_manager import ChatManager, ChatResponse
        from session_manager import SessionManager
        from auth_manager import AuthenticationManager
        
        # Mock dependencies
        mock_client = Mock()
        mock_session_manager = Mock()
        mock_session_manager.is_authenticated.return_value = True
        mock_session_manager.get_user_id.return_value = 'test-user-id'
        
        chat_manager = ChatManager(mock_client, mock_session_manager)
        
        # Mock message store
        chat_manager.message_store = Mock()
        chat_manager.message_store.save_message.return_value = Mock(
            id='test-msg-id',
            user_id='test-user-id',
            role='user',
            content='Test message',
            model_used=None,
            created_at=datetime.now(),
            metadata={}
        )
        
        # Test sending message with conversation ID
        response = chat_manager.send_message(
            user_id='test-user-id',
            message_content='Test message',
            model_type='fast',
            conversation_id='test-conv-id'
        )
        
        assert response.success
        print("✅ ChatManager.send_message() with conversation_id works")
        
        # Test saving assistant response with conversation ID
        response = chat_manager.save_assistant_response(
            user_id='test-user-id',
            response_content='Test response',
            model_used='fast_model',
            conversation_id='test-conv-id'
        )
        
        assert response.success
        print("✅ ChatManager.save_assistant_response() with conversation_id works")
        
        print("✅ ChatManager conversation support tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ ChatManager conversation support test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_migration_sql():
    """Test that the migration SQL is valid"""
    print("\n🧪 Testing database migration SQL...")
    
    try:
        migration_file = Path(__file__).parent / "migrations" / "006_conversation_management.sql"
        
        if not migration_file.exists():
            print("❌ Migration file not found")
            return False
        
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        # Basic SQL validation
        assert 'CREATE TABLE' in sql_content
        assert 'conversations' in sql_content
        assert 'conversation_id' in sql_content
        assert 'get_user_conversations' in sql_content
        
        print("✅ Migration SQL file exists and contains expected content")
        
        # Check for required components
        required_components = [
            'CREATE TABLE IF NOT EXISTS conversations',
            'ALTER TABLE messages ADD COLUMN IF NOT EXISTS conversation_id',
            'CREATE INDEX IF NOT EXISTS idx_conversations_user_id',
            'CREATE OR REPLACE FUNCTION get_user_conversations'
        ]
        
        for component in required_components:
            if component not in sql_content:
                print(f"❌ Missing required component: {component}")
                return False
        
        print("✅ All required migration components found")
        print("✅ Database migration SQL tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database migration SQL test failed: {e}")
        return False

def main():
    """Run all conversation management tests"""
    print("🧬 Pharmacology Chat - Conversation Management Tests")
    print("=" * 60)
    
    tests = [
        test_conversation_manager,
        test_conversation_ui,
        test_message_store_conversation_support,
        test_chat_manager_conversation_support,
        test_database_migration_sql
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All conversation management tests passed!")
        print("\n📋 Next Steps:")
        print("1. Run the database migration using CONVERSATION_MIGRATION_INSTRUCTIONS.md")
        print("2. Restart your Streamlit application")
        print("3. Test the conversation tabs in the UI")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)