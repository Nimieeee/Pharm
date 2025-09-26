"""
ConversationManager class for managing user conversations.
Provides conversation creation, switching, and management functionality.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from supabase import Client
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Conversation:
    """Conversation data model"""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    is_active: bool
    last_message_preview: Optional[str] = None

class ConversationManager:
    """Handles database operations for user conversations"""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize ConversationManager with Supabase client
        
        Args:
            supabase_client: Authenticated Supabase client
        """
        self.client = supabase_client
    
    def create_conversation(self, user_id: str, title: str = "New Conversation") -> Optional[Conversation]:
        """
        Create a new conversation for a user
        
        Args:
            user_id: User's unique identifier
            title: Conversation title
            
        Returns:
            Conversation object if successful, None otherwise
        """
        try:
            conversation_data = {
                'user_id': user_id,
                'title': title,
                'is_active': True
            }
            
            result = self.client.table('conversations').insert(conversation_data).execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                return Conversation(
                    id=data['id'],
                    user_id=data['user_id'],
                    title=data['title'],
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
                    message_count=data.get('message_count', 0),
                    is_active=data.get('is_active', True)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating conversation for user {user_id}: {e}")
            raise
    
    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """
        Get all active conversations for a user
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of Conversation objects ordered by last update (newest first)
        """
        try:
            # Use the database function for efficient querying
            result = self.client.rpc('get_user_conversations', {'user_id': user_id}).execute()
            
            conversations = []
            for data in result.data or []:
                conversations.append(Conversation(
                    id=data['id'],
                    user_id=user_id,
                    title=data['title'],
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
                    message_count=data.get('message_count', 0),
                    is_active=data.get('is_active', True),
                    last_message_preview=data.get('last_message_preview')
                ))
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error getting conversations for user {user_id}: {e}")
            return []
    
    def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Conversation]:
        """
        Get a specific conversation for a user
        
        Args:
            user_id: User's unique identifier
            conversation_id: Conversation's unique identifier
            
        Returns:
            Conversation object if found, None otherwise
        """
        try:
            result = self.client.table('conversations').select('*').eq(
                'id', conversation_id
            ).eq('user_id', user_id).eq('is_active', True).execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                return Conversation(
                    id=data['id'],
                    user_id=data['user_id'],
                    title=data['title'],
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
                    message_count=data.get('message_count', 0),
                    is_active=data.get('is_active', True)
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id} for user {user_id}: {e}")
            return None
    
    def update_conversation_title(self, user_id: str, conversation_id: str, title: str) -> bool:
        """
        Update conversation title
        
        Args:
            user_id: User's unique identifier
            conversation_id: Conversation's unique identifier
            title: New conversation title
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table('conversations').update({
                'title': title,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', conversation_id).eq('user_id', user_id).execute()
            
            return len(result.data or []) > 0
            
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id} title for user {user_id}: {e}")
            return False
    
    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        Soft delete a conversation (mark as inactive)
        
        Args:
            user_id: User's unique identifier
            conversation_id: Conversation's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table('conversations').update({
                'is_active': False,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', conversation_id).eq('user_id', user_id).execute()
            
            return len(result.data or []) > 0
            
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id} for user {user_id}: {e}")
            return False
    
    def get_or_create_default_conversation(self, user_id: str) -> Optional[Conversation]:
        """
        Get the user's default conversation or create one if none exists
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Conversation object for the default conversation
        """
        try:
            # Try to get existing conversations
            conversations = self.get_user_conversations(user_id)
            
            if conversations:
                # Return the most recently updated conversation
                return conversations[0]
            
            # Create a default conversation if none exist
            return self.create_conversation(user_id, "Default Conversation")
            
        except Exception as e:
            logger.error(f"Error getting or creating default conversation for user {user_id}: {e}")
            return None
    
    def generate_conversation_title(self, first_message: str, max_length: int = 50) -> str:
        """
        Generate a conversation title based on the first message
        
        Args:
            first_message: The first user message in the conversation
            max_length: Maximum length for the title
            
        Returns:
            Generated conversation title
        """
        try:
            # Clean and truncate the message
            title = first_message.strip()
            
            # Remove newlines and extra spaces
            title = ' '.join(title.split())
            
            # Truncate if too long
            if len(title) > max_length:
                title = title[:max_length-3] + "..."
            
            # Fallback if empty
            if not title:
                title = "New Conversation"
            
            return title
            
        except Exception as e:
            logger.error(f"Error generating conversation title: {e}")
            return "New Conversation"
    
    def get_conversation_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get conversation statistics for a user
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dictionary with conversation statistics
        """
        try:
            conversations = self.get_user_conversations(user_id)
            
            total_conversations = len(conversations)
            total_messages = sum(conv.message_count for conv in conversations)
            
            # Find most active conversation
            most_active = None
            if conversations:
                most_active = max(conversations, key=lambda c: c.message_count)
            
            return {
                'total_conversations': total_conversations,
                'total_messages': total_messages,
                'most_active_conversation': {
                    'id': most_active.id if most_active else None,
                    'title': most_active.title if most_active else None,
                    'message_count': most_active.message_count if most_active else 0
                } if most_active else None,
                'average_messages_per_conversation': total_messages / total_conversations if total_conversations > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation stats for user {user_id}: {e}")
            return {
                'total_conversations': 0,
                'total_messages': 0,
                'most_active_conversation': None,
                'average_messages_per_conversation': 0
            }