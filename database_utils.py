"""
Database utility functions for user-scoped queries and operations.
Provides secure, user-isolated database operations with comprehensive error handling.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
import time
from supabase import Client
import logging

from error_handler import ErrorHandler, ErrorType, RetryConfig

logger = logging.getLogger(__name__)

class DatabaseUtils:
    """Utility class for user-scoped database operations with comprehensive error handling."""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.error_handler = ErrorHandler()
        self.retry_config = RetryConfig(max_attempts=3, base_delay=1.0, max_delay=10.0)
        self.connection_healthy = True
        self.last_health_check = time.time()
    
    # User management functions
    def create_user_profile(self, user_id: str, email: str, preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a user profile in the users table."""
        try:
            user_data = {
                'id': user_id,
                'email': email,
                'preferences': preferences or {},
                'subscription_tier': 'free'
            }
            
            result = self.client.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating user profile: {e}")
            raise
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user ID."""
        try:
            result = self.client.table('users').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return None
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences."""
        try:
            result = self.client.table('users').update({
                'preferences': preferences
            }).eq('id', user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False
    
    # Message management functions
    def save_message(self, user_id: str, role: str, content: str, model_used: str = None, 
                    metadata: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Save a message for a specific user with error handling and retries."""
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                # Check connection health before operation
                if not self._check_connection_health():
                    raise Exception("Database connection is unhealthy")
                
                message_data = {
                    'user_id': user_id,
                    'role': role,
                    'content': content,
                    'model_used': model_used,
                    'metadata': metadata or {}
                }
                
                result = self.client.table('messages').insert(message_data).execute()
                
                if result.data:
                    logger.debug(f"Message saved successfully for user {user_id}")
                    return result.data[0]
                else:
                    raise Exception("No data returned from insert operation")
                    
            except Exception as e:
                error_info = self.error_handler.handle_error(
                    e, ErrorType.DATABASE, f"save_message_attempt_{attempt}"
                )
                
                if attempt == self.retry_config.max_attempts:
                    logger.error(f"Failed to save message after {attempt} attempts: {str(e)}")
                    # For message saving, we'll return None instead of raising
                    # to allow the application to continue
                    return None
                
                # Wait before retry
                delay = self.error_handler.get_retry_delay(attempt, self.retry_config)
                logger.info(f"Retrying message save in {delay:.1f} seconds")
                time.sleep(delay)
        
        return None
    
    def get_user_messages(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get messages for a specific user with pagination and error handling."""
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                # Check connection health before operation
                if not self._check_connection_health():
                    if attempt == self.retry_config.max_attempts:
                        logger.warning("Database unhealthy, returning empty message list")
                        return []
                    continue
                
                result = self.client.table('messages').select('*').eq('user_id', user_id).order(
                    'created_at', desc=True
                ).limit(limit).offset(offset).execute()
                
                messages = result.data or []
                logger.debug(f"Retrieved {len(messages)} messages for user {user_id}")
                return messages
                
            except Exception as e:
                error_info = self.error_handler.handle_error(
                    e, ErrorType.DATABASE, f"get_user_messages_attempt_{attempt}"
                )
                
                if attempt == self.retry_config.max_attempts:
                    logger.error(f"Failed to get user messages after {attempt} attempts: {str(e)}")
                    return []  # Return empty list instead of raising
                
                # Wait before retry
                delay = self.error_handler.get_retry_delay(attempt, self.retry_config)
                logger.info(f"Retrying get user messages in {delay:.1f} seconds")
                time.sleep(delay)
        
        return []
    
    def get_conversation_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent conversation history for a user."""
        try:
            result = self.client.table('messages').select('*').eq('user_id', user_id).order(
                'created_at', desc=False
            ).limit(limit).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    def clear_user_messages(self, user_id: str) -> bool:
        """Clear all messages for a specific user."""
        try:
            result = self.client.table('messages').delete().eq('user_id', user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error clearing user messages: {e}")
            return False  
  
    # Document management functions
    def save_document(self, user_id: str, content: str, source: str, 
                     embedding: List[float], metadata: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Save a document with embedding for a specific user."""
        try:
            document_data = {
                'user_id': user_id,
                'content': content,
                'source': source,
                'embedding': embedding,
                'metadata': metadata or {}
            }
            
            result = self.client.table('documents').insert(document_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            raise
    
    def get_user_documents(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all documents for a specific user."""
        try:
            result = self.client.table('documents').select('*').eq('user_id', user_id).order(
                'created_at', desc=True
            ).limit(limit).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user documents: {e}")
            return []
    
    def similarity_search(self, user_id: str, query_embedding: List[float], 
                         limit: int = 5, similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Perform similarity search on user's documents using pgvector."""
        try:
            # Use Supabase's vector similarity search with user filtering
            result = self.client.rpc('match_documents', {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': limit,
                'user_id': user_id
            }).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []
    
    def delete_user_document(self, user_id: str, document_id: str) -> bool:
        """Delete a specific document for a user."""
        try:
            result = self.client.table('documents').delete().eq('id', document_id).eq('user_id', user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    def delete_all_user_documents(self, user_id: str) -> bool:
        """Delete all documents for a specific user."""
        try:
            result = self.client.table('documents').delete().eq('user_id', user_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting all user documents: {e}")
            return False
    
    # Utility functions
    def get_user_stats(self, user_id: str) -> Dict[str, int]:
        """Get statistics for a user (message count, document count)."""
        try:
            # Get message count
            message_result = self.client.table('messages').select('id', count='exact').eq('user_id', user_id).execute()
            message_count = message_result.count or 0
            
            # Get document count
            document_result = self.client.table('documents').select('id', count='exact').eq('user_id', user_id).execute()
            document_count = document_result.count or 0
            
            return {
                'message_count': message_count,
                'document_count': document_count
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'message_count': 0, 'document_count': 0}
    
    def health_check(self) -> bool:
        """Check if database connection is healthy."""
        try:
            # Simple query to test connection
            result = self.client.table('users').select('id').limit(1).execute()
            self.connection_healthy = True
            self.last_health_check = time.time()
            logger.debug("Database health check passed")
            return True
        except Exception as e:
            self.connection_healthy = False
            self.last_health_check = time.time()
            logger.error(f"Database health check failed: {e}")
            return False
    
    def _check_connection_health(self) -> bool:
        """Check connection health with caching to avoid excessive checks."""
        current_time = time.time()
        
        # Only check health every 30 seconds to avoid overhead
        if current_time - self.last_health_check < 30:
            return self.connection_healthy
        
        return self.health_check()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status information."""
        is_healthy = self._check_connection_health()
        
        return {
            "healthy": is_healthy,
            "last_check": self.last_health_check,
            "time_since_check": time.time() - self.last_health_check,
            "status": "connected" if is_healthy else "disconnected"
        }
    
    def execute_with_fallback(self, operation_name: str, primary_operation, fallback_operation=None):
        """Execute a database operation with optional fallback."""
        try:
            return primary_operation()
        except Exception as e:
            error_info = self.error_handler.handle_error(
                e, ErrorType.DATABASE, operation_name
            )
            
            if fallback_operation and error_info.fallback_available:
                logger.info(f"Using fallback for {operation_name}")
                try:
                    return fallback_operation()
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for {operation_name}: {str(fallback_error)}")
            
            # If no fallback or fallback failed, return appropriate default
            logger.warning(f"Operation {operation_name} failed, returning default value")
            return None