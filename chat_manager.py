"""
ChatManager for handling conversation flow with user isolation.
Manages chat sessions, message persistence, and conversation history.
"""

from typing import List, Dict, Any, Optional, Generator
from datetime import datetime
import logging
from dataclasses import dataclass
from supabase import Client

from message_store import MessageStore, Message
from session_manager import SessionManager

logger = logging.getLogger(__name__)

@dataclass
class ChatResponse:
    """Response from chat processing"""
    success: bool
    message: Optional[Message] = None
    error_message: Optional[str] = None
    response_content: Optional[str] = None
    model_used: Optional[str] = None

@dataclass
class ConversationContext:
    """Context for a conversation"""
    user_id: str
    messages: List[Message]
    model_preference: str
    total_messages: int

class ChatManager:
    """Manages chat conversations with user isolation and message persistence"""
    
    def __init__(self, supabase_client: Client, session_manager: SessionManager):
        """
        Initialize ChatManager
        
        Args:
            supabase_client: Authenticated Supabase client
            session_manager: Session manager instance
        """
        self.client = supabase_client
        self.session_manager = session_manager
        self.message_store = MessageStore(supabase_client)
    
    def send_message(self, user_id: str, message_content: str, 
                    model_type: str = "fast") -> ChatResponse:
        """
        Process a user message and prepare for AI response
        
        Args:
            user_id: User's unique identifier
            message_content: User's message content
            model_type: AI model type ("fast" or "premium")
            
        Returns:
            ChatResponse with the saved user message
        """
        try:
            print(f"🔍 ChatManager.send_message called with user_id: {user_id}")
            
            # Validate user authentication
            is_authenticated = self.session_manager.is_authenticated()
            print(f"🔍 Is authenticated: {is_authenticated}")
            
            if not is_authenticated:
                return ChatResponse(
                    success=False,
                    error_message="User not authenticated"
                )
            
            # Validate that the user_id matches the session
            session_user_id = self.session_manager.get_user_id()
            print(f"🔍 Session user ID: {session_user_id}")
            
            if session_user_id != user_id:
                return ChatResponse(
                    success=False,
                    error_message=f"User ID mismatch: session={session_user_id}, provided={user_id}"
                )
            
            # Save user message
            print(f"🔍 Attempting to save message to database...")
            user_message = self.message_store.save_message(
                user_id=user_id,
                role="user",
                content=message_content,
                metadata={"model_requested": model_type}
            )
            
            print(f"🔍 Message save result: {user_message is not None}")
            
            if not user_message:
                return ChatResponse(
                    success=False,
                    error_message="Failed to save user message"
                )
            
            print(f"🔍 Message saved successfully with ID: {user_message.id}")
            
            return ChatResponse(
                success=True,
                message=user_message
            )
            
        except Exception as e:
            logger.error(f"Error processing message for user {user_id}: {e}")
            print(f"🔍 Exception in send_message: {e}")
            import traceback
            print(f"🔍 Traceback: {traceback.format_exc()}")
            return ChatResponse(
                success=False,
                error_message=f"Error processing message: {str(e)}"
            )
    
    def save_assistant_response(self, user_id: str, response_content: str, 
                              model_used: str, metadata: Optional[Dict[str, Any]] = None) -> ChatResponse:
        """
        Save an assistant response message
        
        Args:
            user_id: User's unique identifier
            response_content: Assistant's response content
            model_used: AI model that generated the response
            metadata: Additional metadata for the response
            
        Returns:
            ChatResponse with the saved assistant message
        """
        try:
            # Validate user authentication
            if not self.session_manager.is_authenticated():
                return ChatResponse(
                    success=False,
                    error_message="User not authenticated"
                )
            
            # Validate that the user_id matches the session
            session_user_id = self.session_manager.get_user_id()
            if session_user_id != user_id:
                return ChatResponse(
                    success=False,
                    error_message="User ID mismatch"
                )
            
            # Save assistant message
            assistant_message = self.message_store.save_message(
                user_id=user_id,
                role="assistant",
                content=response_content,
                model_used=model_used,
                metadata=metadata or {}
            )
            
            if not assistant_message:
                return ChatResponse(
                    success=False,
                    error_message="Failed to save assistant response"
                )
            
            return ChatResponse(
                success=True,
                message=assistant_message,
                response_content=response_content,
                model_used=model_used
            )
            
        except Exception as e:
            logger.error(f"Error saving assistant response for user {user_id}: {e}")
            return ChatResponse(
                success=False,
                error_message=f"Error saving response: {str(e)}"
            )
    
    def get_conversation_history(self, user_id: str, limit: int = 20) -> List[Message]:
        """
        Get conversation history for a user, filtered by current user
        
        Args:
            user_id: User's unique identifier
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of Message objects in chronological order
        """
        try:
            # Validate user authentication
            if not self.session_manager.is_authenticated():
                logger.warning(f"Unauthenticated request for conversation history")
                return []
            
            # Validate that the user_id matches the session
            session_user_id = self.session_manager.get_user_id()
            if session_user_id != user_id:
                logger.warning(f"User ID mismatch in conversation history request")
                return []
            
            return self.message_store.get_conversation_history(user_id, limit)
            
        except Exception as e:
            logger.error(f"Error getting conversation history for user {user_id}: {e}")
            return []
    
    def clear_conversation(self, user_id: str) -> bool:
        """
        Clear all conversation history for a user
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate user authentication
            if not self.session_manager.is_authenticated():
                return False
            
            # Validate that the user_id matches the session
            session_user_id = self.session_manager.get_user_id()
            if session_user_id != user_id:
                return False
            
            success = self.message_store.delete_user_messages(user_id)
            
            if success:
                logger.info(f"Cleared conversation history for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error clearing conversation for user {user_id}: {e}")
            return False
    
    def get_conversation_context(self, user_id: str, limit: int = 10) -> ConversationContext:
        """
        Get conversation context for AI processing
        
        Args:
            user_id: User's unique identifier
            limit: Maximum number of recent messages to include
            
        Returns:
            ConversationContext with recent messages and metadata
        """
        try:
            # Validate user authentication
            if not self.session_manager.is_authenticated():
                return ConversationContext(
                    user_id=user_id,
                    messages=[],
                    model_preference="fast",
                    total_messages=0
                )
            
            # Validate that the user_id matches the session
            session_user_id = self.session_manager.get_user_id()
            if session_user_id != user_id:
                return ConversationContext(
                    user_id=user_id,
                    messages=[],
                    model_preference="fast",
                    total_messages=0
                )
            
            # Get recent messages
            messages = self.message_store.get_conversation_history(user_id, limit)
            
            # Get total message count
            total_messages = self.message_store.get_message_count(user_id)
            
            # Get user's model preference
            model_preference = self.session_manager.get_model_preference()
            
            return ConversationContext(
                user_id=user_id,
                messages=messages,
                model_preference=model_preference,
                total_messages=total_messages
            )
            
        except Exception as e:
            logger.error(f"Error getting conversation context for user {user_id}: {e}")
            return ConversationContext(
                user_id=user_id,
                messages=[],
                model_preference="fast",
                total_messages=0
            )
    
    def get_user_message_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get message statistics for a user
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dictionary with message statistics
        """
        try:
            # Validate user authentication
            if not self.session_manager.is_authenticated():
                return {"total_messages": 0, "recent_messages": 0}
            
            # Validate that the user_id matches the session
            session_user_id = self.session_manager.get_user_id()
            if session_user_id != user_id:
                return {"total_messages": 0, "recent_messages": 0}
            
            total_messages = self.message_store.get_message_count(user_id)
            recent_messages = len(self.message_store.get_recent_messages(user_id, 24))
            
            return {
                "total_messages": total_messages,
                "recent_messages": recent_messages,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting message stats for user {user_id}: {e}")
            return {"total_messages": 0, "recent_messages": 0}
    
    def validate_user_access(self, user_id: str) -> bool:
        """
        Validate that the current session user can access the specified user's data
        
        Args:
            user_id: User ID to validate access for
            
        Returns:
            True if access is allowed, False otherwise
        """
        try:
            if not self.session_manager.is_authenticated():
                return False
            
            session_user_id = self.session_manager.get_user_id()
            return session_user_id == user_id
            
        except Exception as e:
            logger.error(f"Error validating user access: {e}")
            return False