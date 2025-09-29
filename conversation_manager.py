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
        """Create a new conversation with better error handling"""
        if not title:
            # Use a generic placeholder title that will be updated with first message
            title = "New Chat"
        
        try:
            conversation_id = self.db_manager.create_conversation(title, self.user_session_id)
            
            if conversation_id:
                # Refresh conversations list
                self.load_conversations()
                # Switch to new conversation
                self.switch_conversation(conversation_id)
                # Clear processed files for new conversation
                st.session_state.last_processed_files = []
                return conversation_id
            else:
                # Creation failed, but don't show error to user
                return None
        except Exception as e:
            # Database error - return None to trigger fallback
            print(f"Conversation creation failed: {str(e)}")
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
            
            # Load conversation-specific processed files
            if 'conversation_processed_files' in st.session_state:
                conv_files = st.session_state.conversation_processed_files.get(conversation_id, [])
                st.session_state.last_processed_files = conv_files.copy()
            
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
    
    def update_conversation_title(self, conversation_id: str, new_title: str) -> bool:
        """Update the title of a conversation"""
        try:
            if self.db_manager.client:
                result = self.db_manager.client.table("conversations").update({
                    "title": new_title
                }).eq("id", conversation_id).execute()
                
                if result.data:
                    # Refresh conversations list to show new title
                    self.load_conversations()
                    return True
            return False
        except Exception as e:
            print(f"Error updating conversation title: {str(e)}")
            return False
    
    def generate_title_from_message(self, message: str) -> str:
        """Generate a conversation title from the first user message"""
        # Clean and truncate the message for use as title
        title = message.strip()
        
        # Remove common question words and clean up
        title = title.replace("?", "").replace("!", "").replace(".", "")
        
        # Truncate to reasonable length
        if len(title) > 50:
            title = title[:47] + "..."
        
        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]
        
        return title if title else "New Chat"
    
    def ensure_conversation_exists(self):
        """Ensure there's always a current conversation"""
        try:
            if not st.session_state.current_conversation_id:
                # Load existing conversations
                self.load_conversations()
                
                # If still no current conversation, create one
                if not st.session_state.current_conversation_id:
                    conversation_id = self.create_new_conversation("Welcome Chat")
                    if not conversation_id:
                        # If creation failed, use fallback
                        st.session_state.current_conversation_id = "fallback-conversation"
                        st.session_state.messages = []
                        st.warning("⚠️ Using temporary conversation - database may need setup")
        except Exception as e:
            st.error(f"❌ Error ensuring conversation exists: {str(e)}")
            # Fallback: set a temporary conversation ID to prevent crashes
            st.session_state.current_conversation_id = "fallback-conversation"
            st.session_state.messages = []
    
    def add_message_to_current_conversation(self, role: str, content: str, **metadata):
        """Add a message to the current conversation with robust error handling"""
        # Ensure we have a valid conversation
        if not st.session_state.current_conversation_id:
            self.ensure_conversation_exists()
        
        # Add to session state (always works)
        message = {
            'role': role,
            'content': content,
            'timestamp': time.time(),
            **metadata
        }
        st.session_state.messages.append(message)
        
        # Auto-rename conversation based on first user message
        if (role == "user" and 
            st.session_state.current_conversation_id and 
            st.session_state.current_conversation_id != "fallback-conversation"):
            
            # Check if this is the first user message in the conversation
            user_messages = [msg for msg in st.session_state.messages if msg['role'] == 'user']
            if len(user_messages) == 1:  # This is the first user message
                new_title = self.generate_title_from_message(content)
                self.update_conversation_title(st.session_state.current_conversation_id, new_title)
        
        # Try to save to database only if we have a real conversation ID
        if (st.session_state.current_conversation_id and 
            st.session_state.current_conversation_id != "fallback-conversation"):
            try:
                # Verify conversation exists before saving message
                if self.db_manager.client:
                    # Check if conversation exists
                    result = self.db_manager.client.table("conversations").select("id").eq("id", st.session_state.current_conversation_id).execute()
                    
                    if result.data and len(result.data) > 0:
                        # Conversation exists, safe to save message
                        self.db_manager.store_message(
                            conversation_id=st.session_state.current_conversation_id,
                            role=role,
                            content=content,
                            user_session_id=self.user_session_id,
                            metadata=metadata
                        )
                    else:
                        # Conversation doesn't exist, create a new one
                        new_conversation_id = self.create_new_conversation("Chat Session")
                        if new_conversation_id:
                            st.session_state.current_conversation_id = new_conversation_id
                            # Try saving message again with new conversation
                            self.db_manager.store_message(
                                conversation_id=new_conversation_id,
                                role=role,
                                content=content,
                                user_session_id=self.user_session_id,
                                metadata=metadata
                            )
                        else:
                            # Fall back to session-only storage
                            st.session_state.current_conversation_id = "fallback-conversation"
                            
            except Exception as e:
                # Database error - continue with session-only storage
                # Don't show error to user, just log it silently
                print(f"Database error (continuing with session storage): {str(e)}")
                pass