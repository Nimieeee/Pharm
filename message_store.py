"""
MessageStore class for database operations on user messages.
Provides user-scoped message storage and retrieval functionality.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from supabase import Client
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Message:
    """Message data model"""
    id: str
    user_id: str
    role: str  # "user" or "assistant"
    content: str
    model_used: Optional[str]
    created_at: datetime
    metadata: Dict[str, Any]

class MessageStore:
    """Handles database operations for user messages with user isolation"""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize MessageStore with Supabase client
        
        Args:
            supabase_client: Authenticated Supabase client
        """
        self.client = supabase_client
    
    def save_message(self, user_id: str, role: str, content: str, 
                    model_used: Optional[str] = None, 
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[Message]:
        """
        Save a message for a specific user
        
        Args:
            user_id: User's unique identifier
            role: Message role ("user" or "assistant")
            content: Message content
            model_used: AI model used for assistant messages
            metadata: Additional message metadata
            
        Returns:
            Message object if successful, None otherwise
        """
        try:
            # Validate role
            if role not in ["user", "assistant"]:
                raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")
            
            message_data = {
                'user_id': user_id,
                'role': role,
                'content': content,
                'model_used': model_used,
                'metadata': metadata or {}
            }
            
            result = self.client.table('messages').insert(message_data).execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                return Message(
                    id=data['id'],
                    user_id=data['user_id'],
                    role=data['role'],
                    content=data['content'],
                    model_used=data.get('model_used'),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    metadata=data.get('metadata', {})
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error saving message for user {user_id}: {e}")
            raise
    
    def get_user_messages(self, user_id: str, limit: int = 50, 
                         offset: int = 0) -> List[Message]:
        """
        Get messages for a specific user with pagination
        
        Args:
            user_id: User's unique identifier
            limit: Maximum number of messages to retrieve
            offset: Number of messages to skip
            
        Returns:
            List of Message objects ordered by creation time (newest first)
        """
        try:
            result = self.client.table('messages').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=True).limit(limit).offset(offset).execute()
            
            messages = []
            for data in result.data or []:
                messages.append(Message(
                    id=data['id'],
                    user_id=data['user_id'],
                    role=data['role'],
                    content=data['content'],
                    model_used=data.get('model_used'),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    metadata=data.get('metadata', {})
                ))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages for user {user_id}: {e}")
            return []
    
    def get_conversation_history(self, user_id: str, limit: int = 20) -> List[Message]:
        """
        Get recent conversation history for a user in chronological order
        
        Args:
            user_id: User's unique identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of Message objects ordered by creation time (oldest first)
        """
        try:
            result = self.client.table('messages').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=False).limit(limit).execute()
            
            messages = []
            for data in result.data or []:
                messages.append(Message(
                    id=data['id'],
                    user_id=data['user_id'],
                    role=data['role'],
                    content=data['content'],
                    model_used=data.get('model_used'),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    metadata=data.get('metadata', {})
                ))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history for user {user_id}: {e}")
            return []
    
    def delete_user_messages(self, user_id: str) -> bool:
        """
        Delete all messages for a specific user
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table('messages').delete().eq('user_id', user_id).execute()
            logger.info(f"Deleted messages for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting messages for user {user_id}: {e}")
            return False
    
    def delete_message(self, user_id: str, message_id: str) -> bool:
        """
        Delete a specific message for a user
        
        Args:
            user_id: User's unique identifier
            message_id: Message's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.client.table('messages').delete().eq(
                'id', message_id
            ).eq('user_id', user_id).execute()
            
            return len(result.data or []) > 0
            
        except Exception as e:
            logger.error(f"Error deleting message {message_id} for user {user_id}: {e}")
            return False
    
    def get_message_count(self, user_id: str) -> int:
        """
        Get total message count for a user
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Total number of messages for the user
        """
        try:
            result = self.client.table('messages').select(
                'id', count='exact'
            ).eq('user_id', user_id).execute()
            
            return result.count or 0
            
        except Exception as e:
            logger.error(f"Error getting message count for user {user_id}: {e}")
            return 0
    
    def get_recent_messages(self, user_id: str, hours: int = 24) -> List[Message]:
        """
        Get messages from the last N hours for a user
        
        Args:
            user_id: User's unique identifier
            hours: Number of hours to look back
            
        Returns:
            List of Message objects from the specified time period
        """
        try:
            # Calculate timestamp for N hours ago
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            cutoff_iso = cutoff_time.isoformat() + 'Z'
            
            result = self.client.table('messages').select('*').eq(
                'user_id', user_id
            ).gte('created_at', cutoff_iso).order('created_at', desc=False).execute()
            
            messages = []
            for data in result.data or []:
                messages.append(Message(
                    id=data['id'],
                    user_id=data['user_id'],
                    role=data['role'],
                    content=data['content'],
                    model_used=data.get('model_used'),
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    metadata=data.get('metadata', {})
                ))
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting recent messages for user {user_id}: {e}")
            return []