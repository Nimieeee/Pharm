"""
Integration tests for user-scoped data isolation
Tests that user data is properly isolated across different users
"""

import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import streamlit as st
import uuid
from datetime import datetime
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth_manager import AuthenticationManager, User
from session_manager import SessionManager, UserSession
from message_store import MessageStore, Message
from chat_manager import ChatManager, ChatResponse
from vector_retriever import VectorRetriever, Document
from document_processor import DocumentProcessor


class TestUserDataIsolation(unittest.TestCase):
    """Integration tests for user data isolation"""
    
    def setUp(self):
        """Set up test fixtures with multiple users"""
        # Create mock Supabase client
        self.mock_client = Mock()
        
        # Create test users
        self.user1_id = str(uuid.uuid4())
        self.user2_id = str(uuid.uuid4())
        
        self.user1_email = "user1@example.com"
        self.user2_email = "user2@example.com"
        
        # Create mock auth managers for each user
        self.mock_auth_manager1 = Mock()
        self.mock_auth_manager1.get_current_user.return_value = Mock(
            id=self.user1_id, email=self.user1_email
        )
        
        self.mock_auth_manager2 = Mock()
        self.mock_auth_manager2.get_current_user.return_value = Mock(
            id=self.user2_id, email=self.user2_email
        )
        
        # Create session managers
        self.session_manager1 = SessionManager(self.mock_auth_manager1)
        self.session_manager2 = SessionManager(self.mock_auth_manager2)
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_session_isolation(self, mock_session_state):
        """Test that user sessions are properly isolated"""
        # Initialize sessions for both users
        self.session_manager1.initialize_session(
            self.user1_id, self.user1_email, {'theme': 'light'}
        )
        
        # Store user1 session state
        user1_session = mock_session_state.copy()
        
        # Clear and initialize user2 session
        mock_session_state.clear()
        self.session_manager2.initialize_session(
            self.user2_id, self.user2_email, {'theme': 'dark'}
        )
        
        # Verify sessions are different
        self.assertNotEqual(user1_session['user_session'].user_id, 
                           mock_session_state['user_session'].user_id)
        self.assertNotEqual(user1_session['user_session'].email,
                           mock_session_state['user_session'].email)
        self.assertNotEqual(user1_session['theme'], mock_session_state['theme'])
    
    def test_message_store_isolation(self):
        """Test that message storage is isolated by user"""
        message_store = MessageStore(self.mock_client)
        
        # Mock database responses for different users
        def mock_insert_response(data):
            """Mock insert response based on user_id"""
            mock_result = Mock()
            mock_result.data = [{
                'id': str(uuid.uuid4()),
                'user_id': data['user_id'],
                'role': data['role'],
                'content': data['content'],
                'model_used': data.get('model_used'),
                'created_at': datetime.now().isoformat(),
                'metadata': data.get('metadata', {})
            }]
            return mock_result
        
        def mock_select_response(user_id):
            """Mock select response filtered by user_id"""
            mock_result = Mock()
            if user_id == self.user1_id:
                mock_result.data = [
                    {
                        'id': str(uuid.uuid4()),
                        'user_id': self.user1_id,
                        'role': 'user',
                        'content': 'User 1 message',
                        'model_used': None,
                        'created_at': datetime.now().isoformat(),
                        'metadata': {}
                    }
                ]
            elif user_id == self.user2_id:
                mock_result.data = [
                    {
                        'id': str(uuid.uuid4()),
                        'user_id': self.user2_id,
                        'role': 'user',
                        'content': 'User 2 message',
                        'model_used': None,
                        'created_at': datetime.now().isoformat(),
                        'metadata': {}
                    }
                ]
            else:
                mock_result.data = []
            return mock_result
        
        # Configure mock client
        self.mock_client.table.return_value.insert.return_value.execute.side_effect = \
            lambda: mock_insert_response(self.mock_client.table.return_value.insert.call_args[0][0])
        
        self.mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.side_effect = \
            lambda: mock_select_response(
                self.mock_client.table.return_value.select.return_value.eq.call_args[0][1]
            )
        
        # Save messages for both users
        message1 = message_store.save_message(self.user1_id, 'user', 'User 1 message')
        message2 = message_store.save_message(self.user2_id, 'user', 'User 2 message')
        
        # Verify messages are saved with correct user IDs
        self.assertEqual(message1.user_id, self.user1_id)
        self.assertEqual(message2.user_id, self.user2_id)
        
        # Get conversation history for each user
        history1 = message_store.get_conversation_history(self.user1_id)
        history2 = message_store.get_conversation_history(self.user2_id)
        
        # Verify isolation - each user only sees their own messages
        self.assertEqual(len(history1), 1)
        self.assertEqual(len(history2), 1)
        self.assertEqual(history1[0].user_id, self.user1_id)
        self.assertEqual(history2[0].user_id, self.user2_id)
        self.assertNotEqual(history1[0].content, history2[0].content)
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_chat_manager_isolation(self, mock_session_state):
        """Test that chat manager enforces user isolation"""
        # Initialize sessions
        mock_session_state.clear()
        self.session_manager1.initialize_session(self.user1_id, self.user1_email)
        user1_session_state = mock_session_state.copy()
        
        mock_session_state.clear()
        self.session_manager2.initialize_session(self.user2_id, self.user2_email)
        user2_session_state = mock_session_state.copy()
        
        # Create chat managers
        chat_manager1 = ChatManager(self.mock_client, self.session_manager1)
        chat_manager2 = ChatManager(self.mock_client, self.session_manager2)
        
        # Test user access validation
        with patch('streamlit.session_state', user1_session_state):
            # User 1 can access their own data
            self.assertTrue(chat_manager1.validate_user_access(self.user1_id))
            # User 1 cannot access user 2's data
            self.assertFalse(chat_manager1.validate_user_access(self.user2_id))
        
        with patch('streamlit.session_state', user2_session_state):
            # User 2 can access their own data
            self.assertTrue(chat_manager2.validate_user_access(self.user2_id))
            # User 2 cannot access user 1's data
            self.assertFalse(chat_manager2.validate_user_access(self.user1_id))
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_cross_user_message_prevention(self, mock_session_state):
        """Test that users cannot send messages as other users"""
        # Initialize session for user 1
        self.session_manager1.initialize_session(self.user1_id, self.user1_email)
        
        chat_manager = ChatManager(self.mock_client, self.session_manager1)
        
        # Try to send message as user 2 (should fail)
        response = chat_manager.send_message(self.user2_id, "Unauthorized message")
        
        self.assertFalse(response.success)
        self.assertIn("mismatch", response.error_message.lower())
    
    def test_document_isolation(self):
        """Test that document storage and retrieval is isolated by user"""
        # Mock embedding model
        mock_embedding = Mock()
        mock_embedding.embed_documents.return_value = [[0.1] * 384, [0.2] * 384]
        mock_embedding.embed_query.return_value = [0.1] * 384
        
        # Create document processor and vector retriever
        doc_processor = DocumentProcessor(self.mock_client, mock_embedding)
        vector_retriever = VectorRetriever(self.mock_client, mock_embedding)
        
        # Mock document storage responses
        def mock_upsert_response(documents):
            """Mock upsert response for documents"""
            mock_result = Mock()
            mock_result.data = [
                {'id': doc['id'], 'user_id': doc['user_id']} 
                for doc in documents
            ]
            return mock_result
        
        def mock_rpc_response(user_id):
            """Mock RPC response for vector search filtered by user"""
            mock_result = Mock()
            if user_id == self.user1_id:
                mock_result.data = [
                    {
                        'id': 'doc1',
                        'content': 'User 1 document content',
                        'source': 'user1_doc.pdf',
                        'metadata': {'user_id': self.user1_id},
                        'similarity': 0.85
                    }
                ]
            elif user_id == self.user2_id:
                mock_result.data = [
                    {
                        'id': 'doc2',
                        'content': 'User 2 document content',
                        'source': 'user2_doc.pdf',
                        'metadata': {'user_id': self.user2_id},
                        'similarity': 0.80
                    }
                ]
            else:
                mock_result.data = []
            return mock_result
        
        # Configure mock client
        self.mock_client.table.return_value.upsert.return_value.execute.side_effect = \
            lambda: mock_upsert_response(
                self.mock_client.table.return_value.upsert.call_args[0][0]
            )
        
        self.mock_client.rpc.return_value.execute.side_effect = \
            lambda: mock_rpc_response(
                # Extract user_id from RPC call parameters
                self.mock_client.rpc.call_args[1].get('user_id_param', None)
            )
        
        # Create test documents for each user
        from document_processor import ProcessedDocument
        
        user1_doc = ProcessedDocument(
            id=str(uuid.uuid4()),
            user_id=self.user1_id,
            content="User 1 document content",
            source="user1_doc.pdf",
            metadata={},
            embedding=[0.1] * 384
        )
        
        user2_doc = ProcessedDocument(
            id=str(uuid.uuid4()),
            user_id=self.user2_id,
            content="User 2 document content",
            source="user2_doc.pdf",
            metadata={},
            embedding=[0.2] * 384
        )
        
        # Store documents
        success1 = doc_processor.store_documents([user1_doc])
        success2 = doc_processor.store_documents([user2_doc])
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        
        # Test document retrieval isolation
        user1_docs = vector_retriever.similarity_search("test query", self.user1_id, k=5)
        user2_docs = vector_retriever.similarity_search("test query", self.user2_id, k=5)
        
        # Verify each user only gets their own documents
        self.assertEqual(len(user1_docs), 1)
        self.assertEqual(len(user2_docs), 1)
        self.assertEqual(user1_docs[0].content, "User 1 document content")
        self.assertEqual(user2_docs[0].content, "User 2 document content")
    
    def test_conversation_history_isolation(self):
        """Test that conversation history is isolated between users"""
        # Mock message store responses
        def mock_history_response(user_id):
            """Mock conversation history response filtered by user"""
            if user_id == self.user1_id:
                return [
                    Message(
                        id=str(uuid.uuid4()),
                        user_id=self.user1_id,
                        role='user',
                        content='User 1 question',
                        created_at=datetime.now(),
                        metadata={}
                    ),
                    Message(
                        id=str(uuid.uuid4()),
                        user_id=self.user1_id,
                        role='assistant',
                        content='Response to user 1',
                        created_at=datetime.now(),
                        metadata={}
                    )
                ]
            elif user_id == self.user2_id:
                return [
                    Message(
                        id=str(uuid.uuid4()),
                        user_id=self.user2_id,
                        role='user',
                        content='User 2 question',
                        created_at=datetime.now(),
                        metadata={}
                    )
                ]
            else:
                return []
        
        # Create chat managers with mocked message stores
        chat_manager1 = ChatManager(self.mock_client, self.session_manager1)
        chat_manager2 = ChatManager(self.mock_client, self.session_manager2)
        
        # Mock the get_conversation_history method
        chat_manager1.message_store.get_conversation_history = Mock(
            side_effect=lambda user_id, limit=50: mock_history_response(user_id)
        )
        chat_manager2.message_store.get_conversation_history = Mock(
            side_effect=lambda user_id, limit=50: mock_history_response(user_id)
        )
        
        # Get conversation history for each user
        history1 = chat_manager1.get_conversation_history(self.user1_id)
        history2 = chat_manager2.get_conversation_history(self.user2_id)
        
        # Verify isolation
        self.assertEqual(len(history1), 2)  # User 1 has 2 messages
        self.assertEqual(len(history2), 1)  # User 2 has 1 message
        
        # Verify content isolation
        user1_contents = [msg.content for msg in history1]
        user2_contents = [msg.content for msg in history2]
        
        self.assertIn('User 1 question', user1_contents)
        self.assertIn('Response to user 1', user1_contents)
        self.assertIn('User 2 question', user2_contents)
        
        # Verify no cross-contamination
        self.assertNotIn('User 2 question', user1_contents)
        self.assertNotIn('User 1 question', user2_contents)
    
    @patch('streamlit.session_state', new_callable=dict)
    def test_concurrent_user_sessions(self, mock_session_state):
        """Test handling of concurrent user sessions"""
        # Simulate concurrent sessions by rapidly switching between users
        sessions = {}
        
        # Initialize multiple user sessions
        for i in range(3):
            user_id = f"user_{i}"
            email = f"user{i}@example.com"
            
            mock_session_state.clear()
            mock_auth_manager = Mock()
            mock_auth_manager.get_current_user.return_value = Mock(id=user_id, email=email)
            
            session_manager = SessionManager(mock_auth_manager)
            session_manager.initialize_session(user_id, email, {'theme': f'theme_{i}'})
            
            # Store session state for this user
            sessions[user_id] = mock_session_state.copy()
        
        # Verify each session is unique and isolated
        user_ids = set()
        themes = set()
        
        for user_id, session_state in sessions.items():
            user_session = session_state['user_session']
            user_ids.add(user_session.user_id)
            themes.add(session_state['theme'])
        
        # All user IDs and themes should be unique
        self.assertEqual(len(user_ids), 3)
        self.assertEqual(len(themes), 3)


def run_data_isolation_tests():
    """Run all data isolation tests"""
    print("🔒 Running User Data Isolation Tests")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test class
    tests = unittest.TestLoader().loadTestsFromTestCase(TestUserDataIsolation)
    test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All data isolation tests passed!")
        print("\nData Isolation Features Verified:")
        print("• User session isolation")
        print("• Message storage isolation")
        print("• Chat manager access control")
        print("• Cross-user message prevention")
        print("• Document storage isolation")
        print("• Conversation history isolation")
        print("• Concurrent session handling")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False


if __name__ == "__main__":
    success = run_data_isolation_tests()
    exit(0 if success else 1)