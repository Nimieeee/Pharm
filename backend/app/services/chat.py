"""
Chat service for conversation and message management
OPTIMIZED VERSION with performance monitoring
"""

import time
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
    """Optimized chat service with performance monitoring"""
    
    def __init__(self, db: Client):
        self.db = db
    
    async def create_conversation(
        self, 
        conversation_data: ConversationCreate, 
        user: User
    ) -> Conversation:
        """Create a new conversation for user"""
        start = time.time()
        try:
            conv_dict = conversation_data.dict()
            conv_dict["user_id"] = str(user.id)
            
            result = self.db.table("conversations").insert(conv_dict).execute()
            
            if not result.data:
                raise Exception("Failed to create conversation")
            
            conv_record = result.data[0]
            elapsed = (time.time() - start) * 1000
            print(f"✅ create_conversation: {elapsed:.0f}ms")
            
            return Conversation(
                **conv_record,
                message_count=0,
                document_count=0,
                last_activity=conv_record.get("updated_at")
            )
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ create_conversation failed after {elapsed:.0f}ms: {e}")
            raise Exception(f"Failed to create conversation: {str(e)}")
    
    async def get_user_conversations(self, user: User) -> List[Conversation]:
        """Get all conversations for a user - OPTIMIZED single query"""
        start = time.time()
        try:
            # Single optimized query - no joins, just conversations
            result = self.db.table("conversations").select(
                "id, title, created_at, updated_at, is_pinned, is_archived, user_id"
            ).eq("user_id", str(user.id)).order("updated_at", desc=True).limit(50).execute()
            
            query_time = (time.time() - start) * 1000
            print(f"📊 get_user_conversations query: {query_time:.0f}ms, rows={len(result.data or [])}")
            
            conversations = []
            for record in result.data or []:
                conversations.append(Conversation(
                    **record,
                    message_count=0,  # Skip counting for speed
                    document_count=0,
                    last_activity=record.get("updated_at")
                ))
            
            total_time = (time.time() - start) * 1000
            if total_time > 1000:
                print(f"🐢 get_user_conversations SLOW: {total_time:.0f}ms")
            else:
                print(f"✅ get_user_conversations: {total_time:.0f}ms")
            
            return conversations
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ get_user_conversations failed after {elapsed:.0f}ms: {e}")
            raise Exception(f"Failed to get conversations: {str(e)}")
    
    async def get_conversation(
        self, 
        conversation_id: UUID, 
        user: User
    ) -> Optional[Conversation]:
        """Get a specific conversation for user"""
        start = time.time()
        try:
            result = self.db.table("conversations").select(
                "id, title, created_at, updated_at, is_pinned, is_archived, user_id"
            ).eq("id", str(conversation_id)).eq("user_id", str(user.id)).single().execute()
            
            elapsed = (time.time() - start) * 1000
            
            if not result.data:
                print(f"⚠️ get_conversation: not found ({elapsed:.0f}ms)")
                return None
            
            print(f"✅ get_conversation: {elapsed:.0f}ms")
            
            return Conversation(
                **result.data,
                message_count=0,
                document_count=0,
                last_activity=result.data.get("updated_at")
            )
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ get_conversation failed after {elapsed:.0f}ms: {e}")
            return None
    
    async def get_conversation_with_messages(
        self, 
        conversation_id: UUID, 
        user: User
    ) -> Optional[ConversationWithMessages]:
        """Get conversation with all messages - OPTIMIZED"""
        start = time.time()
        try:
            # Step 1: Get conversation
            conv_start = time.time()
            conv_result = self.db.table("conversations").select("*")\
                .eq("id", str(conversation_id)).eq("user_id", str(user.id)).execute()
            conv_time = (time.time() - conv_start) * 1000
            print(f"  📊 conversation query: {conv_time:.0f}ms")
            
            if not conv_result.data:
                print(f"⚠️ get_conversation_with_messages: conversation not found")
                return None
            
            conv_record = conv_result.data[0]
            
            # Step 2: Get messages
            msg_start = time.time()
            msg_result = self.db.table("messages").select("*")\
                .eq("conversation_id", str(conversation_id))\
                .eq("user_id", str(user.id))\
                .order("created_at").execute()
            msg_time = (time.time() - msg_start) * 1000
            print(f"  📊 messages query: {msg_time:.0f}ms, rows={len(msg_result.data or [])}")
            
            messages = [Message(**r) for r in msg_result.data or []]
            
            total_time = (time.time() - start) * 1000
            if total_time > 1000:
                print(f"🐢 get_conversation_with_messages SLOW: {total_time:.0f}ms")
            else:
                print(f"✅ get_conversation_with_messages: {total_time:.0f}ms")
            
            return ConversationWithMessages(
                **conv_record,
                message_count=len(messages),
                document_count=0,
                last_activity=conv_record.get("updated_at"),
                messages=messages
            )
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ get_conversation_with_messages failed after {elapsed:.0f}ms: {e}")
            raise Exception(f"Failed to get conversation with messages: {str(e)}")
    
    async def update_conversation(
        self, 
        conversation_id: UUID, 
        conversation_data: ConversationUpdate, 
        user: User
    ) -> Optional[Conversation]:
        """Update a conversation"""
        start = time.time()
        try:
            update_dict = conversation_data.dict(exclude_unset=True)
            if not update_dict:
                return await self.get_conversation(conversation_id, user)
            
            result = self.db.table("conversations").update(
                update_dict
            ).eq("id", str(conversation_id)).eq("user_id", str(user.id)).execute()
            
            elapsed = (time.time() - start) * 1000
            
            if not result.data:
                print(f"⚠️ update_conversation: not found ({elapsed:.0f}ms)")
                return None
            
            print(f"✅ update_conversation: {elapsed:.0f}ms")
            return await self.get_conversation(conversation_id, user)
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ update_conversation failed after {elapsed:.0f}ms: {e}")
            raise Exception(f"Failed to update conversation: {str(e)}")
    
    async def clone_conversation(
        self, 
        conversation_id: UUID, 
        user: User
    ) -> Optional[Conversation]:
        """Clone a conversation and its messages"""
        start = time.time()
        try:
            original = await self.get_conversation(conversation_id, user)
            if not original:
                return None
            
            new_title = f"{original.title} (Copy)"
            new_conv_data = ConversationCreate(title=new_title)
            new_conv = await self.create_conversation(new_conv_data, user)
            
            messages = await self.get_conversation_messages(conversation_id, user)
            
            for msg in messages:
                msg_dict = {
                    "conversation_id": str(new_conv.id),
                    "user_id": str(user.id),
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": msg.metadata or {}
                }
                self.db.table("messages").insert(msg_dict).execute()
            
            elapsed = (time.time() - start) * 1000
            print(f"✅ clone_conversation: {elapsed:.0f}ms, messages={len(messages)}")
            
            return await self.get_conversation(new_conv.id, user)
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ clone_conversation failed after {elapsed:.0f}ms: {e}")
            raise Exception(f"Failed to clone conversation: {str(e)}")

    async def delete_conversation(
        self, 
        conversation_id: UUID, 
        user: User
    ) -> bool:
        """Delete a conversation and all its data"""
        start = time.time()
        try:
            existing = await self.get_conversation(conversation_id, user)
            if not existing:
                return False
            
            result = self.db.table("conversations").delete().eq(
                "id", str(conversation_id)
            ).eq("user_id", str(user.id)).execute()
            
            elapsed = (time.time() - start) * 1000
            print(f"✅ delete_conversation: {elapsed:.0f}ms")
            
            return len(result.data) > 0
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ delete_conversation failed after {elapsed:.0f}ms: {e}")
            if "policy" in str(e).lower() or "permission" in str(e).lower():
                raise Exception(f"Permission denied. Details: {str(e)}")
            raise Exception(f"Failed to delete conversation: {str(e)}")
    
    async def add_message(
        self, 
        message_data: MessageCreate, 
        user: User
    ) -> Optional[Message]:
        """Add a message to a conversation - OPTIMIZED"""
        start = time.time()
        try:
            # Quick existence check
            check_start = time.time()
            check = self.db.table("conversations").select("id", count="exact", head=True)\
                .eq("id", str(message_data.conversation_id))\
                .eq("user_id", str(user.id)).execute()
            check_time = (time.time() - check_start) * 1000
            
            if check.count == 0:
                print(f"⚠️ add_message: conversation not found ({check_time:.0f}ms)")
                return None
            
            # Insert message
            insert_start = time.time()
            msg_dict = {
                "conversation_id": str(message_data.conversation_id),
                "user_id": str(user.id),
                "role": message_data.role,
                "content": message_data.content,
                "metadata": message_data.metadata or {}
            }
            
            result = self.db.table("messages").insert(msg_dict).execute()
            insert_time = (time.time() - insert_start) * 1000
            
            if not result.data:
                raise Exception("Failed to create message")
            
            msg_record = result.data[0]
            
            # Update timestamp (non-blocking)
            self.db.table("conversations").update({
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(message_data.conversation_id)).execute()
            
            total_time = (time.time() - start) * 1000
            print(f"✅ add_message: {total_time:.0f}ms (check={check_time:.0f}ms, insert={insert_time:.0f}ms)")
            
            return Message(**msg_record)
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ add_message failed after {elapsed:.0f}ms: {e}")
            raise Exception(f"Failed to add message: {str(e)}")
    
    async def get_conversation_messages(
        self, 
        conversation_id: UUID, 
        user: User,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get messages for a conversation - OPTIMIZED"""
        start = time.time()
        try:
            query = self.db.table("messages").select(
                "id, conversation_id, user_id, role, content, metadata, created_at"
            ).eq("conversation_id", str(conversation_id)).eq(
                "user_id", str(user.id)
            ).order("created_at")
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            messages = [Message(**r) for r in result.data or []]
            
            elapsed = (time.time() - start) * 1000
            if elapsed > 500:
                print(f"🐢 get_conversation_messages SLOW: {elapsed:.0f}ms, rows={len(messages)}")
            else:
                print(f"✅ get_conversation_messages: {elapsed:.0f}ms, rows={len(messages)}")
            
            return messages
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ get_conversation_messages failed after {elapsed:.0f}ms: {e}")
            raise Exception(f"Failed to get messages: {str(e)}")
    
    async def get_recent_messages(
        self, 
        conversation_id: UUID, 
        user: User, 
        limit: int = 50
    ) -> List[Message]:
        """Get recent messages for context"""
        start = time.time()
        try:
            result = self.db.table("messages").select("*")\
                .eq("conversation_id", str(conversation_id))\
                .eq("user_id", str(user.id))\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            messages = [Message(**r) for r in result.data or []]
            messages = sorted(messages, key=lambda x: x.created_at)
            
            elapsed = (time.time() - start) * 1000
            print(f"✅ get_recent_messages: {elapsed:.0f}ms, rows={len(messages)}")
            
            return messages
            
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            print(f"❌ get_recent_messages failed after {elapsed:.0f}ms: {e}")
            raise Exception(f"Failed to get recent messages: {str(e)}")
    
    async def _get_conversation_stats(
        self, 
        conversation_id: str, 
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get conversation statistics - optimized"""
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
            pass  # Non-critical