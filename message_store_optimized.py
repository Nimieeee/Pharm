"""
Optimized MessageStore with pagination, caching, and performance improvements
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import uuid
from supabase import Client
import logging
from dataclasses import dataclass

from message_store import Message, MessageStore
from performance_optimizer import performance_optimizer, PaginationHelper

logger = logging.getLogger(__name__)

@dataclass
class MessagePage:
    """Paginated message result"""
    messages: List[Message]
    pagination_info: Dict[str, Any]
    total_count: int
    cache_hit: bool = False

class OptimizedMessageStore(MessageStore):
    """Enhanced MessageStore with pagination, caching, and performance optimizations"""
    
    def __init__(self, supabase_client: Client):
        """Initialize optimized message store"""
        super().__init__(supabase_client)
        self.cache_ttl = 300  # 5 minutes cache TTL
    
    def get_paginated_messages(self, user_id: str, page: int = 1, page_size: int = 20) -> MessagePage:
        """
        Get paginated messages for a user with caching
        
        Args:
            user_id: User's unique identifier
            page: Page number (1-based)
            page_size: Number of messages per page
            
        Returns:
            MessagePage with paginated results
        """
        cache_key = f"messages_page:{user_id}:{page}:{page_size}"
        
        # Try cache first
        cached_result = performance_optimizer.get_cached_user_data(user_id, f"messages_page_{page}_{page_size}")
        if cached_result:
            logger.debug(f"Cache hit for paginated messages: {cache_key}")
            cached_result.cache_hit = True
            return cached_result
        
        try:
            # Get total count first (with caching)
            total_count = self.get_cached_message_count(user_id)
            
            # Calculate pagination
            total_pages = max(1, (total_count + page_size - 1) // page_size)
            page = max(1, min(page, total_pages))
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Fetch messages from database
            result = self.client.table('messages').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=True).limit(page_size).offset(offset).execute()
            
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
            
            # Create pagination info
            pagination_info = {
                "current_page": page,
                "total_pages": total_pages,
                "page_size": page_size,
                "total_items": total_count,
                "has_previous": page > 1,
                "has_next": page < total_pages
            }
            
            message_page = MessagePage(
                messages=messages,
                pagination_info=pagination_info,
                total_count=total_count,
                cache_hit=False
            )
            
            # Cache the result
            performance_optimizer.set_cached_user_data(
                user_id, 
                f"messages_page_{page}_{page_size}", 
                message_page, 
                ttl=self.cache_ttl
            )
            
            logger.info(f"Fetched page {page} of messages for user {user_id} ({len(messages)} messages)")
            return message_page
            
        except Exception as e:
            logger.error(f"Error getting paginated messages for user {user_id}: {e}")
            return MessagePage(
                messages=[],
                pagination_info={
                    "current_page": 1,
                    "total_pages": 1,
                    "page_size": page_size,
                    "total_items": 0,
                    "has_previous": False,
                    "has_next": False
                },
                total_count=0
            )
    
    def get_cached_message_count(self, user_id: str) -> int:
        """Get message count with caching"""
        cache_key = f"message_count:{user_id}"
        
        # Try cache first
        cached_count = performance_optimizer.get_cached_user_data(user_id, "message_count")
        if cached_count is not None:
            return cached_count
        
        # Fetch from database
        count = self.get_message_count(user_id)
        
        # Cache with shorter TTL since this changes frequently
        performance_optimizer.set_cached_user_data(user_id, "message_count", count, ttl=60)
        
        return count
    
    def get_recent_conversation_history(self, user_id: str, limit: int = 10) -> List[Message]:
        """
        Get recent conversation history with caching
        
        Args:
            user_id: User's unique identifier
            limit: Maximum number of recent messages
            
        Returns:
            List of recent Message objects in chronological order
        """
        cache_key = f"recent_history:{user_id}:{limit}"
        
        # Try cache first
        cached_messages = performance_optimizer.get_cached_user_data(user_id, f"recent_history_{limit}")
        if cached_messages:
            logger.debug(f"Cache hit for recent conversation history: {cache_key}")
            return cached_messages
        
        try:
            # Fetch recent messages
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
            
            # Cache with shorter TTL for recent messages
            performance_optimizer.set_cached_user_data(
                user_id, 
                f"recent_history_{limit}", 
                messages, 
                ttl=60  # 1 minute TTL for recent messages
            )
            
            logger.debug(f"Fetched {len(messages)} recent messages for user {user_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting recent conversation history for user {user_id}: {e}")
            return []
    
    def save_message(self, user_id: str, role: str, content: str, 
                    model_used: Optional[str] = None, 
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[Message]:
        """
        Save a message and invalidate relevant caches
        
        Args:
            user_id: User's unique identifier
            role: Message role ("user" or "assistant")
            content: Message content
            model_used: AI model used for assistant messages
            metadata: Additional message metadata
            
        Returns:
            Message object if successful, None otherwise
        """
        # Save message using parent method
        message = super().save_message(user_id, role, content, model_used, metadata)
        
        if message:
            # Invalidate caches that would be affected by new message
            self._invalidate_message_caches(user_id)
            logger.debug(f"Invalidated caches after saving message for user {user_id}")
        
        return message
    
    def delete_user_messages(self, user_id: str) -> bool:
        """
        Delete all messages for a user and invalidate caches
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        success = super().delete_user_messages(user_id)
        
        if success:
            # Invalidate all caches for this user
            performance_optimizer.invalidate_user_cache(user_id)
            logger.info(f"Cleared all caches after deleting messages for user {user_id}")
        
        return success
    
    def get_message_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive message statistics with caching
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Dictionary with message statistics
        """
        cache_key = f"message_stats:{user_id}"
        
        # Try cache first
        cached_stats = performance_optimizer.get_cached_user_data(user_id, "message_stats")
        if cached_stats:
            return cached_stats
        
        try:
            # Get basic counts
            total_messages = self.get_cached_message_count(user_id)
            recent_messages = len(self.get_recent_messages(user_id, 24))
            
            # Get model usage statistics
            model_stats = self._get_model_usage_stats(user_id)
            
            # Get activity statistics
            activity_stats = self._get_activity_stats(user_id)
            
            stats = {
                "total_messages": total_messages,
                "recent_messages": recent_messages,
                "user_messages": model_stats.get("user_messages", 0),
                "assistant_messages": model_stats.get("assistant_messages", 0),
                "models_used": model_stats.get("models_used", {}),
                "first_message_date": activity_stats.get("first_message_date"),
                "last_message_date": activity_stats.get("last_message_date"),
                "most_active_day": activity_stats.get("most_active_day"),
                "avg_messages_per_day": activity_stats.get("avg_messages_per_day", 0)
            }
            
            # Cache with medium TTL
            performance_optimizer.set_cached_user_data(user_id, "message_stats", stats, ttl=180)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting message statistics for user {user_id}: {e}")
            return {
                "total_messages": 0,
                "recent_messages": 0,
                "error": str(e)
            }
    
    def _get_model_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get model usage statistics"""
        try:
            result = self.client.table('messages').select(
                'role, model_used'
            ).eq('user_id', user_id).execute()
            
            user_messages = 0
            assistant_messages = 0
            models_used = {}
            
            for data in result.data or []:
                if data['role'] == 'user':
                    user_messages += 1
                elif data['role'] == 'assistant':
                    assistant_messages += 1
                    model = data.get('model_used', 'unknown')
                    models_used[model] = models_used.get(model, 0) + 1
            
            return {
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "models_used": models_used
            }
            
        except Exception as e:
            logger.error(f"Error getting model usage stats: {e}")
            return {}
    
    def _get_activity_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user activity statistics"""
        try:
            result = self.client.table('messages').select(
                'created_at'
            ).eq('user_id', user_id).order('created_at', desc=False).execute()
            
            if not result.data:
                return {}
            
            dates = [datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')).date() 
                    for data in result.data]
            
            first_date = dates[0] if dates else None
            last_date = dates[-1] if dates else None
            
            # Count messages per day
            day_counts = {}
            for date in dates:
                day_counts[date] = day_counts.get(date, 0) + 1
            
            most_active_day = max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None
            
            # Calculate average messages per day
            if first_date and last_date:
                days_active = (last_date - first_date).days + 1
                avg_per_day = len(dates) / days_active
            else:
                avg_per_day = 0
            
            return {
                "first_message_date": first_date.isoformat() if first_date else None,
                "last_message_date": last_date.isoformat() if last_date else None,
                "most_active_day": most_active_day.isoformat() if most_active_day else None,
                "avg_messages_per_day": round(avg_per_day, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting activity stats: {e}")
            return {}
    
    def get_all_user_messages(self, user_id: str) -> List[Message]:
        """
        Get all messages for a user without pagination limits
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            List of all Message objects ordered chronologically (oldest first)
        """
        cache_key = f"all_messages:{user_id}"
        
        # Try cache first
        cached_messages = performance_optimizer.get_cached_user_data(user_id, "all_messages")
        if cached_messages is not None:
            logger.debug(f"Cache hit for all messages: {cache_key}")
            return cached_messages
        
        try:
            # Fetch all messages from database without limits
            result = self.client.table('messages').select('*').eq(
                'user_id', user_id
            ).order('created_at', desc=False).execute()  # Oldest first for chronological display
            
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
            
            # Cache the result with shorter TTL for unlimited messages to ensure freshness
            performance_optimizer.set_cached_user_data(
                user_id, 
                "all_messages", 
                messages, 
                ttl=60  # 1 minute cache for unlimited messages
            )
            
            logger.info(f"Loaded {len(messages)} unlimited messages for user {user_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting all messages for user {user_id}: {e}")
            return []
    
    def _invalidate_message_caches(self, user_id: str) -> None:
        """Invalidate message-related caches for a user"""
        # Invalidate specific cache types that would be affected by new messages
        cache_patterns = [
            "message_count",
            "recent_history_",
            "messages_page_",
            "message_stats",
            "all_messages"  # Add unlimited messages cache
        ]
        
        for pattern in cache_patterns:
            # This is a simplified approach - in a real implementation,
            # you might want to track cache keys more precisely
            performance_optimizer.set_cached_user_data(user_id, pattern, None, ttl=0)