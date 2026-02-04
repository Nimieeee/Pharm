"""
Chat Service - CLEAN REWRITE
Simple, reliable conversation and message management
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
    """Simple, reliable chat service"""
    
    def __init__(self, db: Client):
        self.db = db
    
    # =====================
    # CONVERSATION METHODS
    # =====================
    
    async def create_conversation(self, conversation_data: ConversationCreate, user: User) -> Conversation:
        """Create a new conversation"""
        start = time.time()
        try:
            data = {
                "title": conversation_data.title,
                "user_id": str(user.id)
            }
            
            result = self.db.table("conversations").insert(data).execute()
            
            if not result.data:
                raise Exception("No data returned from insert")
            
            record = result.data[0]
            print(f"✅ create_conversation: {(time.time()-start)*1000:.0f}ms")
            
            return Conversation(
                id=record["id"],
                title=record["title"],
                user_id=record["user_id"],
                created_at=record["created_at"],
                updated_at=record["updated_at"],
                is_pinned=record.get("is_pinned", False),
                is_archived=record.get("is_archived", False),
                message_count=0,
                document_count=0,
                last_activity=record["updated_at"]
            )
        except Exception as e:
            print(f"❌ create_conversation failed: {e}")
            raise
    
    async def get_user_conversations(self, user: User) -> List[Conversation]:
        """Get all conversations for user - simple and fast"""
        start = time.time()
        try:
            result = self.db.table("conversations").select("id, title, user_id, created_at, updated_at, is_pinned, is_archived, title_translations")\
                .eq("user_id", str(user.id))\
                .order("updated_at", desc=True)\
                .limit(50)\
                .execute()
            
            # --- TRANSLATION LOGIC ---
            from app.services.translation import translation_service
            import asyncio
            
            target_lang = getattr(user, 'language', 'en')
            conversations = []
            convs_needing_translation = []

            for r in result.data or []:
                conv_obj = Conversation(
                    id=r["id"],
                    title=r["title"],
                    user_id=r["user_id"],
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    is_pinned=r.get("is_pinned", False),
                    is_archived=r.get("is_archived", False),
                    message_count=0,
                    document_count=0,
                    last_activity=r["updated_at"],
                    title_translations=r.get("title_translations") or {}
                )
                conversations.append(conv_obj)
                
                # Check if title translation needed
                if target_lang != 'en' and (not conv_obj.title_translations or target_lang not in conv_obj.title_translations):
                    convs_needing_translation.append(conv_obj)
            
            # Run translations in parallel (if any)
            if convs_needing_translation:
                print(f"🌍 Translating {len(convs_needing_translation)} titles to {target_lang}...")
                
                async def translate_title_and_update(conv):
                    try:
                        translated_title = await translation_service.translate_text(conv.title, target_lang)
                        if translated_title:
                            # Update in memory
                            if not conv.title_translations: conv.title_translations = {}
                            conv.title_translations[target_lang] = translated_title
                            
                            # Persist to DB asynchronously
                            self.db.table("conversations").update({
                                "title_translations": conv.title_translations
                            }).eq("id", str(conv.id)).execute()
                    except Exception as e:
                        print(f"⚠️ Title translation task error: {e}")
                
                # Create tasks
                translation_tasks = [translate_title_and_update(c) for c in convs_needing_translation]
                try:
                    await asyncio.gather(*translation_tasks)
                except Exception as e:
                    print(f"❌ Gather error: {e}")

            print(f"✅ get_user_conversations: {(time.time()-start)*1000:.0f}ms, count={len(conversations)}")
            return conversations
            
        except Exception as e:
            print(f"❌ get_user_conversations failed: {e}")
            raise
    
    async def get_conversation(self, conversation_id: UUID, user: User) -> Optional[Conversation]:
        """Get a single conversation"""
        start = time.time()
        try:
            result = self.db.table("conversations").select("*")\
                .eq("id", str(conversation_id))\
                .eq("user_id", str(user.id))\
                .execute()
            
            if not result.data:
                print(f"⚠️ get_conversation: not found")
                return None
            
            r = result.data[0]
            print(f"✅ get_conversation: {(time.time()-start)*1000:.0f}ms")
            
            return Conversation(
                id=r["id"],
                title=r["title"],
                user_id=r["user_id"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                is_pinned=r.get("is_pinned", False),
                is_archived=r.get("is_archived", False),
                message_count=0,
                document_count=0,
                last_activity=r["updated_at"]
            )
            
        except Exception as e:
            print(f"❌ get_conversation failed: {e}")
            return None
    
    async def get_conversation_with_messages(self, conversation_id: UUID, user: User) -> Optional[ConversationWithMessages]:
        """Get conversation with all its messages"""
        start = time.time()
        try:
            # Get conversation
            conv = await self.get_conversation(conversation_id, user)
            if not conv:
                return None
            
            # Get messages
            messages = await self.get_conversation_messages(conversation_id, user)
            
            print(f"✅ get_conversation_with_messages: {(time.time()-start)*1000:.0f}ms, msgs={len(messages)}")
            
            return ConversationWithMessages(
                id=conv.id,
                title=conv.title,
                user_id=conv.user_id,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                is_pinned=conv.is_pinned,
                is_archived=conv.is_archived,
                message_count=len(messages),
                document_count=0,
                last_activity=conv.updated_at,
                messages=messages
            )
            
        except Exception as e:
            print(f"❌ get_conversation_with_messages failed: {e}")
            raise
    
    async def update_conversation(self, conversation_id: UUID, data: ConversationUpdate, user: User) -> Optional[Conversation]:
        """Update a conversation"""
        start = time.time()
        try:
            update_dict = data.dict(exclude_unset=True)
            if not update_dict:
                return await self.get_conversation(conversation_id, user)
            
            result = self.db.table("conversations").update(update_dict)\
                .eq("id", str(conversation_id))\
                .eq("user_id", str(user.id))\
                .execute()
            
            if not result.data:
                return None
            
            print(f"✅ update_conversation: {(time.time()-start)*1000:.0f}ms")
            return await self.get_conversation(conversation_id, user)
            
        except Exception as e:
            print(f"❌ update_conversation failed: {e}")
            raise
    
    async def delete_conversation(self, conversation_id: UUID, user: User) -> bool:
        """Delete a conversation"""
        start = time.time()
        try:
            # Verify ownership first
            conv = await self.get_conversation(conversation_id, user)
            if not conv:
                return False
            
            result = self.db.table("conversations").delete()\
                .eq("id", str(conversation_id))\
                .eq("user_id", str(user.id))\
                .execute()
            
            print(f"✅ delete_conversation: {(time.time()-start)*1000:.0f}ms")
            return True
            
        except Exception as e:
            print(f"❌ delete_conversation failed: {e}")
            return False
    
    async def clone_conversation(self, conversation_id: UUID, user: User) -> Optional[Conversation]:
        """Clone a conversation with its messages"""
        try:
            original = await self.get_conversation(conversation_id, user)
            if not original:
                return None
            
            # Create new conversation
            new_conv = await self.create_conversation(
                ConversationCreate(title=f"{original.title} (Copy)"),
                user
            )
            
            # Copy messages
            messages = await self.get_conversation_messages(conversation_id, user)
            for msg in messages:
                await self.add_message(
                    MessageCreate(
                        conversation_id=new_conv.id,
                        role=msg.role,
                        content=msg.content,
                        metadata=msg.metadata
                    ),
                    user
                )
            
            return new_conv
            
        except Exception as e:
            print(f"❌ clone_conversation failed: {e}")
            raise
    
    # ================
    # MESSAGE METHODS
    # ================
    
    async def add_message(self, message_data: MessageCreate, user: User) -> Optional[Message]:
        """Add a message - SIMPLE DIRECT INSERT"""
        start = time.time()
        try:
            data = {
                "conversation_id": str(message_data.conversation_id),
                "user_id": str(user.id),
                "role": message_data.role,
                "content": message_data.content,
                "metadata": message_data.metadata or {}
            }
            
            print(f"💾 add_message: conv={message_data.conversation_id}, role={message_data.role}")
            
            result = self.db.table("messages").insert(data).execute()
            
            if not result.data:
                print(f"❌ add_message: no data returned")
                return None
            
            record = result.data[0]
            
            # Update conversation timestamp
            try:
                self.db.table("conversations").update({
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(message_data.conversation_id)).execute()
            except:
                pass  # Non-critical
            
            print(f"✅ add_message: {(time.time()-start)*1000:.0f}ms, id={record['id']}")
            
            return Message(
                id=record["id"],
                conversation_id=record["conversation_id"],
                user_id=record["user_id"],
                role=record["role"],
                content=record["content"],
                metadata=record.get("metadata", {}),
                created_at=record["created_at"]
            )
            
        except Exception as e:
            print(f"❌ add_message failed: {e}")
            # Don't raise - return None so streaming can continue
            return None
    
    async def get_conversation_messages(self, conversation_id: UUID, user: User, limit: Optional[int] = None) -> List[Message]:
        """Get messages for a conversation, translating if needed"""
        start = time.time()
        try:
            query = self.db.table("messages").select("*")\
                .eq("conversation_id", str(conversation_id))\
                .eq("user_id", str(user.id))\
                .order("created_at")
            
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            
            messages = []
            
            # --- TRANSLATION LOGIC ---
            from app.services.translation import translation_service
            import asyncio
            
            target_lang = getattr(user, 'language', 'en')
            print(f"🔍 DEBUG translation: target_lang={target_lang}, user.id={user.id}")
            tasks = []
            messages_needing_translation = []
            
            print(f"🔍 DEBUG: Entering loop with {len(result.data)} items. Type: {type(result.data)}")
            for i, r in enumerate(result.data or []):
                print(f"  > Processing item {i}")
                try:
                    msg_obj = Message(
                        id=r["id"],
                        conversation_id=r["conversation_id"],
                        role=r["role"],
                        content=r["content"],
                        metadata=r.get("metadata", {}),
                        translations=r.get("translations") or {},  # Ensure dict
                        created_at=r["created_at"]
                    )
                    messages.append(msg_obj)
                    print(f"  > Appended. Messages count: {len(messages)}")
                except Exception as e:
                    print(f"❌ DEBUG: Failed to create Message object: {e} | Data: {r}")
                
                # Check if translation needed (skip if English or already present)
                if target_lang != 'en' and (not msg_obj.translations or target_lang not in msg_obj.translations):
                    messages_needing_translation.append(msg_obj)
            
            print(f"🔍 DEBUG: Loop finished. Messages: {len(messages)}")

            # Run translations in parallel (if any)
            if messages_needing_translation:
                print(f"🌍 Translating {len(messages_needing_translation)} messages to {target_lang}...")
                
                async def translate_and_update(msg):
                    try:
                        translated_text = await translation_service.translate_text(msg.content, target_lang)
                        if translated_text:
                            # Update in memory
                            if not msg.translations: msg.translations = {}
                            msg.translations[target_lang] = translated_text
                            
                            # Persist to DB asynchronously
                            self.db.table("messages").update({
                                "translations": msg.translations
                            }).eq("id", str(msg.id)).execute()
                    except Exception as e:
                        print(f"⚠️ Translation task error: {e}")
                
                # Create tasks
                translation_tasks = [translate_and_update(m) for m in messages_needing_translation]
                # Allow up to 2 seconds for translations, otherwise return originals (don't block forever)
                # Actually, user wants them changed. Let's wait.
                try:
                    await asyncio.gather(*translation_tasks)
                except Exception as e:
                    print(f"❌ Gather error: {e}")
                print(f"✅ Translations complete")

            print(f"✅ get_conversation_messages: {(time.time()-start)*1000:.0f}ms, count={len(messages)}")
            return messages
            
        except Exception as e:
            print(f"❌ get_conversation_messages failed: {e}")
            return []
    
    async def get_recent_messages(self, conversation_id: UUID, user: User, limit: int = 20) -> List[Message]:
        """Get recent messages for AI context"""
        start = time.time()
        try:
            result = self.db.table("messages").select("*")\
                .eq("conversation_id", str(conversation_id))\
                .eq("user_id", str(user.id))\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            messages = []
            for r in result.data or []:
                messages.append(Message(
                    id=r["id"],
                    conversation_id=r["conversation_id"],
                    user_id=r["user_id"],
                    role=r["role"],
                    content=r["content"],
                    metadata=r.get("metadata", {}),
                    created_at=r["created_at"]
                ))
            
            # Reverse to get chronological order
            messages.reverse()
            
            print(f"✅ get_recent_messages: {(time.time()-start)*1000:.0f}ms, count={len(messages)}")
            return messages
            
        except Exception as e:
            print(f"❌ get_recent_messages failed: {e}")
            return []
    
    # ===============
    # HELPER METHODS
    # ===============
    
    async def _get_conversation_stats(self, conversation_id: str, user_id: UUID) -> Dict[str, Any]:
        """Placeholder for stats"""
        return {"message_count": 0, "document_count": 0, "last_activity": None}
    
    async def _update_conversation_timestamp(self, conversation_id: UUID):
        """Update conversation timestamp"""
        try:
            self.db.table("conversations").update({
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(conversation_id)).execute()
        except:
            pass