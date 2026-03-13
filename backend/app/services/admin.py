"""
Admin service for system management
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
from supabase import Client

from app.models.user import User, UserProfile
from app.models.conversation import Conversation
from app.models.support import SupportRequest


class AdminService:
    """Admin service for system management and monitoring"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics"""
        try:
            # Get user stats
            users_result = self.db.table("users").select("id, created_at, is_active").execute()
            users_data = users_result.data or []
            
            total_users = len(users_data)
            active_users = len([u for u in users_data if u.get("is_active", True)])
            
            # Users created in last 30 days
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            new_users = len([
                u for u in users_data 
                if u.get("created_at", "") > thirty_days_ago
            ])
            
            # Get conversation stats
            conversations_result = self.db.table("conversations").select("id, created_at").execute()
            conversations_data = conversations_result.data or []
            
            total_conversations = len(conversations_data)
            new_conversations = len([
                c for c in conversations_data 
                if c.get("created_at", "") > thirty_days_ago
            ])
            
            # Get message stats
            messages_result = self.db.table("messages").select("id, created_at").execute()
            messages_data = messages_result.data or []
            
            total_messages = len(messages_data)
            new_messages = len([
                m for m in messages_data 
                if m.get("created_at", "") > thirty_days_ago
            ])
            
            # Get document stats
            documents_result = self.db.table("document_chunks").select("id, created_at").execute()
            documents_data = documents_result.data or []
            
            total_documents = len(documents_data)
            new_documents = len([
                d for d in documents_data 
                if d.get("created_at", "") > thirty_days_ago
            ])
            
            # Get support request stats
            support_result = self.db.table("support_requests").select("id, status, created_at").execute()
            support_data = support_result.data or []
            
            total_support_requests = len(support_data)
            open_support_requests = len([
                s for s in support_data 
                if s.get("status") == "open"
            ])
            
            return {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "new_this_month": new_users
                },
                "conversations": {
                    "total": total_conversations,
                    "new_this_month": new_conversations
                },
                "messages": {
                    "total": total_messages,
                    "new_this_month": new_messages
                },
                "documents": {
                    "total": total_documents,
                    "new_this_month": new_documents
                },
                "support": {
                    "total": total_support_requests,
                    "open": open_support_requests
                },
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Failed to get system stats: {str(e)}")
    
    async def get_all_users(
        self, 
        limit: Optional[int] = None, 
        offset: int = 0,
        search: Optional[str] = None
    ) -> List[UserProfile]:
        """Get all users with profiles"""
        try:
            query = self.db.table("users").select("*").order("created_at", desc=True)
            
            if limit:
                query = query.limit(limit)
            
            if offset:
                query = query.offset(offset)
            
            result = query.execute()
            users_data = result.data or []
            
            # Filter by search if provided
            if search:
                search_lower = search.lower()
                users_data = [
                    u for u in users_data 
                    if (search_lower in u.get("email", "").lower() or
                        search_lower in u.get("first_name", "").lower() or
                        search_lower in u.get("last_name", "").lower())
                ]
            
            # Get conversation counts for each user
            users = []
            for user_data in users_data:
                # Get conversation count
                conv_result = self.db.table("conversations").select(
                    "id"
                ).eq("user_id", user_data["id"]).execute()
                
                conversation_count = len(conv_result.data or [])
                
                user_profile = UserProfile(
                    **user_data,
                    conversation_count=conversation_count
                )
                users.append(user_profile)
            
            return users
            
        except Exception as e:
            raise Exception(f"Failed to get users: {str(e)}")
    
    async def get_user_details(self, user_id: UUID) -> Optional[UserProfile]:
        """Get detailed user information"""
        try:
            # Get user
            user_result = self.db.table("users").select("*").eq("id", str(user_id)).execute()
            
            if not user_result.data:
                return None
            
            user_data = user_result.data[0]
            
            # Get conversation count
            conv_result = self.db.table("conversations").select(
                "id"
            ).eq("user_id", str(user_id)).execute()
            
            conversation_count = len(conv_result.data or [])
            
            return UserProfile(
                **user_data,
                conversation_count=conversation_count
            )
            
        except Exception as e:
            raise Exception(f"Failed to get user details: {str(e)}")
    
    async def update_user_status(self, user_id: UUID, is_active: bool) -> bool:
        """Update user active status"""
        try:
            result = self.db.table("users").update({
                "is_active": is_active
            }).eq("id", str(user_id)).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            raise Exception(f"Failed to update user status: {str(e)}")
    
    async def get_all_conversations(
        self, 
        limit: Optional[int] = None, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all conversations with user info"""
        try:
            query = self.db.table("conversations").select(
                "*, users(email, first_name, last_name)"
            ).order("updated_at", desc=True)
            
            if limit:
                query = query.limit(limit)
            
            if offset:
                query = query.offset(offset)
            
            result = query.execute()
            conversations_data = result.data or []
            
            # Format conversations with stats
            conversations = []
            for conv_data in conversations_data:
                # Get message count
                msg_result = self.db.table("messages").select(
                    "id"
                ).eq("conversation_id", conv_data["id"]).execute()
                
                message_count = len(msg_result.data or [])
                
                # Get document count
                doc_result = self.db.table("document_chunks").select(
                    "id"
                ).eq("conversation_id", conv_data["id"]).execute()
                
                document_count = len(doc_result.data or [])
                
                conversation = {
                    "id": conv_data["id"],
                    "title": conv_data["title"],
                    "user_id": conv_data["user_id"],
                    "user_email": conv_data.get("users", {}).get("email", "Unknown"),
                    "user_name": f"{conv_data.get('users', {}).get('first_name', '')} {conv_data.get('users', {}).get('last_name', '')}".strip(),
                    "message_count": message_count,
                    "document_count": document_count,
                    "created_at": conv_data["created_at"],
                    "updated_at": conv_data["updated_at"]
                }
                conversations.append(conversation)
            
            return conversations
            
        except Exception as e:
            raise Exception(f"Failed to get conversations: {str(e)}")
    
    async def delete_user_data(self, user_id: UUID) -> bool:
        """Delete all user data (conversations, messages, documents)"""
        try:
            # Delete user (cascades to conversations, messages, document_chunks)
            result = self.db.table("users").delete().eq("id", str(user_id)).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            raise Exception(f"Failed to delete user data: {str(e)}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get system health information"""
        try:
            # Test database connection
            db_healthy = True
            try:
                self.db.table("users").select("id").limit(1).execute()
            except Exception:
                db_healthy = False
            
            # Get recent activity
            one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            
            # Recent messages
            recent_messages_result = self.db.table("messages").select(
                "id"
            ).gte("created_at", one_hour_ago).execute()
            
            recent_messages = len(recent_messages_result.data or [])
            
            # Recent users
            recent_users_result = self.db.table("users").select(
                "id"
            ).gte("created_at", one_hour_ago).execute()
            
            recent_users = len(recent_users_result.data or [])
            
            return {
                "status": "healthy" if db_healthy else "unhealthy",
                "database": {
                    "connected": db_healthy,
                    "last_check": datetime.utcnow().isoformat()
                },
                "activity": {
                    "recent_messages": recent_messages,
                    "recent_users": recent_users,
                    "period": "last_hour"
                },
                "uptime": "Available",  # Could be enhanced with actual uptime tracking
                "version": "2.0.0"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }