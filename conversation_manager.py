"""
Conversation Management for Multi-Conversation Support
Handles conversation creation, switching, and management
"""

import streamlit as st
from typing import Optional, List, Dict, Any
from database import SimpleChatbotDB
import time


class ConversationManager:
    """Manages multiple conversations with separate knowledge bases"""
    
    def __init__(self, db_manager: SimpleChatbotDB, user_session_id: str = None):
        self.db_manager = db_manager
        self.user_session_id = user_session_id or "anonymous"
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize conversation-related session state"""
        if 'current_conversation_id' not in st.session_state:
            st.session_state.current_conversation_id = None
        
        if 'conversations' not in st.session_state:
            st.session_state.conversations = []
        
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        
        if 'last_processed_files' not in st.session_state:
            st.session_state.last_processed_files = []
    
    def create_new_conversation(self, title: str = None) -> Optional[str]:
        """Create a new conversation"""
        if not title:
            # Generate a default title with timestamp
            title = f"New Chat {time.strftime('%m/%d %H:%M')}"
        
        conversation_id = self.db_manager.create_conversation(title, self.user_session_id)
        
        if conversation_id:
            # Refresh conversations list
            self.load_conversations()
            # Switch to new conversation
            self.switch_conversation(conversation_id)
            st.success(f"✅ Created new conversation: {title}")
            return conversation_id
        else:
            st.error("❌ Failed to create new conversation")
            return None
    
    def load_conversations(self):
        """Load all conversations from database for this user session"""
        conversations = self.db_manager.get_conversations(self.user_session_id)
        st.session_state.conversations = conversations
        
        # If no current conversation and conversations exist, select the first one
        if not st.session_state.current_conversation_id and conversations:
            st.session_state.current_conversation_id = conversations[0]['id']
    
    def switch_conversation(self, conversation_id: str):
        """Switch to a different conversation"""
        if conversation_id != st.session_state.current_conversation_id:
            # Save current state if needed
            self._save_current_conversation_state()
            
            # Switch conversation
            st.session_state.current_conversation_id = conversation_id
            
            # Load messages for new conversation
            self._load_conversation_messages(conversation_id)
            
            # Reset processed files for new conversation
            st.session_state.last_processed_files = []
            
            # Update conversation timestamp
            self.db_manager.update_conversation_timestamp(conversation_id)
    
    def _save_current_conversation_state(self):
        """Save current conversation messages to database"""
        if not st.session_state.current_conversation_id:
            return
        
        # Get existing messages from database to avoid duplicates
        existing_messages = self.db_manager.get_conversation_messages(
            st.session_state.current_conversation_id,
            self.user_session_id
        )
        existing_count = len(existing_messages)
        
        # Save any new messages that aren't in database yet
        session_messages = st.session_state.messages
        for i, message in enumerate(session_messages[existing_count:], existing_count):
            self.db_manager.store_message(
                conversation_id=st.session_state.current_conversation_id,
                role=message['role'],
                content=message['content'],
                user_session_id=self.user_session_id,
                metadata={
                    'timestamp': message.get('timestamp', time.time()),
                    'model': message.get('model', 'unknown'),
                    'context_used': message.get('context_used', False),
                    'context_chunks': message.get('context_chunks', 0),
                    'error': message.get('error', False)
                }
            )
    
    def _load_conversation_messages(self, conversation_id: str):
        """Load messages for a conversation from database"""
        db_messages = self.db_manager.get_conversation_messages(conversation_id, self.user_session_id)
        
        # Convert database messages to session format
        session_messages = []
        for msg in db_messages:
            session_message = {
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg.get('created_at'),
            }
            
            # Add metadata if available
            metadata = msg.get('metadata', {})
            if metadata:
                session_message.update({
                    'model': metadata.get('model', 'unknown'),
                    'context_used': metadata.get('context_used', False),
                    'context_chunks': metadata.get('context_chunks', 0),
                    'error': metadata.get('error', False)
                })
            
            session_messages.append(session_message)
        
        st.session_state.messages = session_messages
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        if self.db_manager.delete_conversation(conversation_id):
            # If we deleted the current conversation, switch to another or create new
            if conversation_id == st.session_state.current_conversation_id:
                self.load_conversations()
                if st.session_state.conversations:
                    self.switch_conversation(st.session_state.conversations[0]['id'])
                else:
                    # No conversations left, create a new one
                    self.create_new_conversation()
            else:
                # Just refresh the conversations list
                self.load_conversations()
            
            st.success("✅ Conversation deleted")
            return True
        else:
            st.error("❌ Failed to delete conversation")
            return False
    
    def get_current_conversation_title(self) -> str:
        """Get the title of the current conversation"""
        if not st.session_state.current_conversation_id:
            return "No Conversation"
        
        for conv in st.session_state.conversations:
            if conv['id'] == st.session_state.current_conversation_id:
                return conv['title']
        
        return "Unknown Conversation"
    
    def get_conversation_stats(self, conversation_id: str) -> Dict[str, Any]:
        """Get statistics for a conversation"""
        return self.db_manager.get_conversation_stats(conversation_id, self.user_session_id)
    
    def ensure_conversation_exists(self):
        """Ensure there's always a current conversation"""
        try:
            if not st.session_state.current_conversation_id:
                # Load existing conversations
                self.load_conversations()
                
                # If still no current conversation, create one
                if not st.session_state.current_conversation_id:
                    self.create_new_conversation("Welcome Chat")
        except Exception as e:
            st.error(f"❌ Error ensuring conversation exists: {str(e)}")
            # Fallback: set a temporary conversation ID to prevent crashes
            st.session_state.current_conversation_id = "temp-conversation"
            st.session_state.messages = []
    
    def add_message_to_current_conversation(self, role: str, content: str, **metadata):
        """Add a message to the current conversation"""
        if not st.session_state.current_conversation_id:
            self.ensure_conversation_exists()
        
        # Add to session state
        message = {
            'role': role,
            'content': content,
            'timestamp': time.time(),
            **metadata
        }
        st.session_state.messages.append(message)
        
        # Save to database
        self.db_manager.store_message(
            conversation_id=st.session_state.current_conversation_id,
            role=role,
            content=content,
            user_session_id=self.user_session_id,
            metadata=metadata
        )