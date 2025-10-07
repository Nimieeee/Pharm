"""
Chat service for conversation and message management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from supabase import Client

from app.models.conversation import (
    Conversation, ConversationCreate, ConversationUpdate, ConversationWithMessages,
    Message, MessageCreate
)
from app.models.user import User


class ChatService:
    """Chat service for managing conversations and messages"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def create_conversation(
        self, 
        conversation_data: ConversationCreate, 
        user: User
    ) -> Conversation:
        """Create a new conversation for user"""
        try:
            # Insert conversation
            conv_dict = conversation_data.dict()
            conv_dict["user_id"] = str(user.id)
            
            result = self.db.table("conversations").insert(conv_dict).execute()
            
            if not result.data:
                raise Exception("Failed to create conversation")
            
            conv_record = result.data[0]
            
            # Get conversation stats
            stats = await self._get_conversation_stats(conv_record["id"], user.id)
            
            return Conversation(
                **conv_record,
                message_count=stats["message_count"],
                document_count=stats["document_count"],
                last_activity=stats["last_activity"]
            )
            
        except Exception as e:
            raise Exception(f"Failed to create conversation: {str(e)}")
    
    async def get_user_conversations(self, user: User) -> List[Conversation]:
        """Get all conversations for a user"""
        try:
            result = self.db.table("conversations").select(
                "*"
            ).eq("user_id", str(user.id)).order("updated_at", desc=True).execute()
            
            conversations = []
            for conv_record in result.data or []:
                # Get conversation stats
                stats = await self._get_conversation_stats(conv_record["id"], user.id)
                
                conversation = Conversation(
                    **conv_record,
                    message_count=stats["message_count"],
                    document_count=stats["document_count"],
                    last_activity=stats["last_activity"]
                )
                conversations.append(conversation)
            
            return conversations
            
        except Exception as e:
            raise Exception(f"Failed to get conversations: {str(e)}")
    
    async def get_conversation(
        self, 
        conversation_id: UUID, 
        user: User
    ) -> Optional[Conversation]:
        """Get a specific conversation for user"""
        try:
            result = self.db.table("conversations").select(
                "*"
            ).eq("id", str(conversation_id)).eq("user_id", str(user.id)).execute()
            
            if not result.data:
                return None
            
            conv_record = result.data[0]
            
            # Get conversation stats
            stats = await self._get_conversation_stats(conversation_id, user.id)
            
            return Conversation(
                **conv_record,
                message_count=stats["message_count"],
                document_count=stats["document_count"],
                last_activity=stats["last_activity"]
            )
            
        except Exception as e:
            raise Exception(f"Failed to get conversation: {str(e)}")
    
    async def get_conversation_with_messages(
        self, 
        conversation_id: UUID, 
        user: User
    ) -> Optional[ConversationWithMessages]:
        """Get conversation with all messages"""
        try:
            # Get conversation
            conversation = await self.get_conversation(conversation_id, user)
            if not conversation:
                return None
            
            # Get messages
            messages = await self.get_conversation_messages(conversation_id, user)
            
            return ConversationWithMessages(
                **conversation.dict(),
                messages=messages
            )
            
        except Exception as e:
            raise Exception(f"Failed to get conversation with messages: {str(e)}")
    
    async def update_conversation(
        self, 
        conversation_id: UUID, 
        conversation_data: ConversationUpdate, 
        user: User
    ) -> Optional[Conversation]:
        """Update a conversation"""
        try:
            # Check if conversation exists and belongs to user
            existing = await self.get_conversation(conversation_id, user)
            if not existing:
                return None
            
            # Update conversation
            update_dict = conversation_data.dict(exclude_unset=True)
            if not update_dict:
                return existing
            
            result = self.db.table("conversations").update(
                update_dict
            ).eq("id", str(conversation_id)).eq("user_id", str(user.id)).execute()
            
            if not result.data:
                return None
            
            # Return updated conversation
            return await self.get_conversation(conversation_id, user)
            
        except Exception as e:
            raise Exception(f"Failed to update conversation: {str(e)}")
    
    async def delete_conversation(
        self, 
        conversation_id: UUID, 
        user: User
    ) -> bool:
        """Delete a conversation and all its data"""
        try:
            # Check if conversation exists and belongs to user
            existing = await self.get_conversation(conversation_id, user)
            if not existing:
                return False
            
            # Delete conversation (cascades to messages and document_chunks)
            result = self.db.table("conversations").delete().eq(
                "id", str(conversation_id)
            ).eq("user_id", str(user.id)).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            raise Exception(f"Failed to delete conversation: {str(e)}")
    
    async def add_message(
        self, 
        message_data: MessageCreate, 
        user: User
    ) -> Optional[Message]:
        """Add a message to a conversation"""
        try:
            # Check if conversation exists and belongs to user
            conversation = await self.get_conversation(message_data.conversation_id, user)
            if not conversation:
                return None
            
            # Insert message - convert UUIDs to strings for JSON serialization
            msg_dict = {
                "conversation_id": str(message_data.conversation_id),
                "user_id": str(user.id),
                "role": message_data.role,
                "content": message_data.content,
                "metadata": message_data.metadata or {}
            }
            
            result = self.db.table("messages").insert(msg_dict).execute()
            
            if not result.data:
                raise Exception("Failed to create message")
            
            msg_record = result.data[0]
            
            # Update conversation timestamp
            await self._update_conversation_timestamp(message_data.conversation_id)
            
            return Message(**msg_record)
            
        except Exception as e:
            raise Exception(f"Failed to add message: {str(e)}")
    
    async def get_conversation_messages(
        self, 
        conversation_id: UUID, 
        user: User,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get messages for a conversation"""
        try:
            # Check if conversation belongs to user
            conversation = await self.get_conversation(conversation_id, user)
            if not conversation:
                return []
            
            query = self.db.table("messages").select(
                "*"
            ).eq("conversation_id", str(conversation_id)).eq(
                "user_id", str(user.id)
            ).order("created_at")
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            messages = []
            for msg_record in result.data or []:
                message = Message(**msg_record)
                messages.append(message)
            
            return messages
            
        except Exception as e:
            raise Exception(f"Failed to get messages: {str(e)}")
    
    async def get_recent_messages(
        self, 
        conversation_id: UUID, 
        user: User, 
        limit: int = 50
    ) -> List[Message]:
        """Get recent messages for context"""
        try:
            messages = await self.get_conversation_messages(conversation_id, user)
            return messages[-limit:] if messages else []
            
        except Exception as e:
            raise Exception(f"Failed to get recent messages: {str(e)}")
    
    async def _get_conversation_stats(
        self, 
        conversation_id: str, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            result = self.db.rpc('get_conversation_stats', {
                'conversation_uuid': conversation_id,
                'user_session_uuid': str(user_id)
            }).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            
            return {
                "message_count": 0,
                "document_count": 0,
                "last_activity": None
            }
            
        except Exception:
            return {
                "message_count": 0,
                "document_count": 0,
                "last_activity": None
            }
    
    async def _update_conversation_timestamp(self, conversation_id: UUID):
        """Update conversation's updated_at timestamp"""
        try:
            self.db.table("conversations").update({
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(conversation_id)).execute()
        except Exception:
            pass  # Non-critical operation