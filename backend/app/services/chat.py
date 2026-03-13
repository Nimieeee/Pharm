
"""
Chat Service - CLEAN REWRITE
Simple, reliable conversation and message management
"""

import time
import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from supabase import Client

from app.core.database import async_db_execute
from app.models.conversation import (
    Conversation, ConversationCreate, ConversationUpdate, ConversationWithMessages,
    Message, MessageCreate
)
from app.models.user import User

logger = logging.getLogger(__name__)

# Max translations to run inline before returning (prevents blocking on large convos)
MAX_INLINE_TRANSLATIONS = 5


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
            
            result = await async_db_execute(
                lambda: self.db.table("conversations").insert(data).execute()
            )
            
            if not result.data:
                raise Exception("No data returned from insert")
            
            record = result.data[0]
            logger.debug(f"create_conversation: {(time.time()-start)*1000:.0f}ms")
            
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
            logger.error(f"create_conversation failed: {e}")
            raise
    
    async def get_user_conversations(self, user: User) -> List[Conversation]:
        """Get all conversations for user - simple and fast"""
        start = time.time()
        try:
            uid = str(user.id)
            result = await async_db_execute(
                lambda: self.db.table("conversations").select("id, title, user_id, created_at, updated_at, is_pinned, is_archived, title_translations")\
                    .eq("user_id", uid)\
                    .order("updated_at", desc=True)\
                    .limit(50)\
                    .execute()
            )
            
            # --- TRANSLATION LOGIC ---
            from app.services.translation import translation_service
            
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
                
                if (not conv_obj.title_translations or target_lang not in conv_obj.title_translations):
                    convs_needing_translation.append(conv_obj)
            
            # Translate titles — cap batch to avoid blocking the response
            if convs_needing_translation:
                batch = convs_needing_translation[:MAX_INLINE_TRANSLATIONS]
                logger.info(f"Translating {len(batch)}/{len(convs_needing_translation)} titles to {target_lang}")
                
                async def translate_title_and_update(conv):
                    try:
                        translated_title = await translation_service.translate_text(conv.title, target_lang)
                        if translated_title:
                            if not conv.title_translations: conv.title_translations = {}
                            conv.title_translations[target_lang] = translated_title
                            
                            conv_id = str(conv.id)
                            translations = conv.title_translations
                            await async_db_execute(
                                lambda: self.db.table("conversations").update({
                                    "title_translations": translations
                                }).eq("id", conv_id).execute()
                            )
                    except Exception as e:
                        logger.warning(f"Title translation task error: {e}")
                
                translation_tasks = [translate_title_and_update(c) for c in batch]
                try:
                    await asyncio.gather(*translation_tasks)
                except Exception as e:
                    logger.error(f"Title translation gather error: {e}")
                
                # Fire-and-forget remaining translations in background
                remaining = convs_needing_translation[MAX_INLINE_TRANSLATIONS:]
                if remaining:
                    async def translate_remaining():
                        for c in remaining:
                            await translate_title_and_update(c)
                    asyncio.create_task(translate_remaining())

            logger.debug(f"get_user_conversations: {(time.time()-start)*1000:.0f}ms, count={len(conversations)}")
            return conversations
            
        except Exception as e:
            logger.error(f"get_user_conversations failed: {e}")
            raise
    
    async def get_conversation(self, conversation_id: UUID, user: User) -> Optional[Conversation]:
        """Get a single conversation"""
        start = time.time()
        try:
            conv_id = str(conversation_id)
            uid = str(user.id)
            result = await async_db_execute(
                lambda: self.db.table("conversations").select("*")\
                    .eq("id", conv_id)\
                    .eq("user_id", uid)\
                    .execute()
            )
            
            if not result.data:
                return None
            
            r = result.data[0]
            logger.debug(f"get_conversation: {(time.time()-start)*1000:.0f}ms")
            
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
            logger.error(f"get_conversation failed: {e}")
            return None
    
    async def get_conversation_with_messages(self, conversation_id: UUID, user: User) -> Optional[ConversationWithMessages]:
        """Get conversation with all its messages"""
        start = time.time()
        try:
            conv = await self.get_conversation(conversation_id, user)
            if not conv:
                return None
            
            messages = await self.get_conversation_messages(conversation_id, user)
            
            logger.debug(f"get_conversation_with_messages: {(time.time()-start)*1000:.0f}ms, msgs={len(messages)}")
            
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
            logger.error(f"get_conversation_with_messages failed: {e}")
            raise
    
    async def update_conversation(self, conversation_id: UUID, data: ConversationUpdate, user: User) -> Optional[Conversation]:
        """Update a conversation"""
        start = time.time()
        try:
            update_dict = data.dict(exclude_unset=True)
            if not update_dict:
                return await self.get_conversation(conversation_id, user)
            
            conv_id = str(conversation_id)
            uid = str(user.id)
            result = await async_db_execute(
                lambda: self.db.table("conversations").update(update_dict)\
                    .eq("id", conv_id)\
                    .eq("user_id", uid)\
                    .execute()
            )
            
            if not result.data:
                return None
            
            logger.debug(f"update_conversation: {(time.time()-start)*1000:.0f}ms")
            return await self.get_conversation(conversation_id, user)
            
        except Exception as e:
            logger.error(f"update_conversation failed: {e}")
            raise
    
    async def delete_conversation(self, conversation_id: UUID, user: User) -> bool:
        """Delete a conversation"""
        start = time.time()
        try:
            conv = await self.get_conversation(conversation_id, user)
            if not conv:
                return False
            
            conv_id = str(conversation_id)
            uid = str(user.id)
            await async_db_execute(
                lambda: self.db.table("conversations").delete()\
                    .eq("id", conv_id)\
                    .eq("user_id", uid)\
                    .execute()
            )
            
            logger.debug(f"delete_conversation: {(time.time()-start)*1000:.0f}ms")
            return True
            
        except Exception as e:
            logger.error(f"delete_conversation failed: {e}")
            return False
    
    async def clone_conversation(self, conversation_id: UUID, user: User) -> Optional[Conversation]:
        """Clone a conversation with its messages (batch insert)"""
        try:
            original = await self.get_conversation(conversation_id, user)
            if not original:
                return None
            
            # Create new conversation
            new_conv = await self.create_conversation(
                ConversationCreate(title=f"{original.title} (Copy)"),
                user
            )
            
            # Copy messages — BATCH insert instead of N+1
            messages = await self.get_conversation_messages(conversation_id, user)
            if messages:
                batch_data = []
                for msg in messages:
                    batch_data.append({
                        "conversation_id": str(new_conv.id),
                        "user_id": str(user.id),
                        "role": msg.role,
                        "content": msg.content,
                        "metadata": msg.metadata or {}
                    })
                
                await async_db_execute(
                    lambda: self.db.table("messages").insert(batch_data).execute()
                )
            
            return new_conv
            
        except Exception as e:
            logger.error(f"clone_conversation failed: {e}")
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
            
            # Include parent_id for DAG branching if provided
            if message_data.parent_id:
                data["parent_id"] = str(message_data.parent_id)
            
            logger.debug(f"add_message: conv={message_data.conversation_id}, role={message_data.role}")
            
            result = await async_db_execute(
                lambda: self.db.table("messages").insert(data).execute()
            )
            
            if not result.data:
                logger.error("add_message: no data returned")
                return None
            
            record = result.data[0]
            
            # Update conversation timestamp (non-critical)
            try:
                conv_id = str(message_data.conversation_id)
                ts = datetime.utcnow().isoformat()
                await async_db_execute(
                    lambda: self.db.table("conversations").update({
                        "updated_at": ts
                    }).eq("id", conv_id).execute()
                )
            except Exception:
                pass  # Non-critical
            
            logger.debug(f"add_message: {(time.time()-start)*1000:.0f}ms, id={record['id']}")
            
            return Message(
                id=record["id"],
                conversation_id=record["conversation_id"],
                user_id=record["user_id"],
                role=record["role"],
                content=record["content"],
                metadata=record.get("metadata", {}),
                parent_id=record.get("parent_id"),
                created_at=record["created_at"]
            )
            
        except Exception as e:
            logger.error(f"add_message failed: {e}")
            # Don't raise - return None so streaming can continue
            return None

    async def update_message_content(self, message_id: UUID, content: str, user: User, metadata: dict = None) -> bool:
        """Update the content (and optionally metadata) of an existing message."""
        try:
            msg_id = str(message_id)
            uid = str(user.id)
            
            logger.info(f"📝 update_message_content: msg_id={msg_id}, user_id={uid}, content_len={len(content)}")
            
            # First, fetch the message to verify it exists and get user_id
            try:
                fetch_result = await async_db_execute(
                    lambda: self.db.table("messages").select("id, user_id, conversation_id").eq("id", msg_id).execute()
                )
                
                if not fetch_result.data or len(fetch_result.data) == 0:
                    logger.error(f"❌ update_message_content: Message {msg_id} not found in database")
                    return False
                
                msg_data = fetch_result.data[0]
                msg_user_id = msg_data.get('user_id')
                
                # Check if the user owns this message
                if msg_user_id != uid:
                    logger.error(f"❌ update_message_content: User {uid} does not own message {msg_id} (owner: {msg_user_id})")
                    return False
                    
                logger.info(f"✅ update_message_content: Message found, user ownership verified")
                
            except Exception as fetch_error:
                logger.error(f"❌ update_message_content: Fetch failed: {fetch_error}")
                return False
            
            # Prepare update data
            update_data = {"content": content}
            if metadata is not None:
                update_data["metadata"] = metadata
            
            logger.debug(f"📝 update_message_content: Executing update query")
            
            # Execute update
            result = await async_db_execute(
                lambda: self.db.table("messages").update(
                    update_data
                ).eq("id", msg_id).eq("user_id", uid).execute()
            )
            
            # Check result
            if result.data and len(result.data) > 0:
                logger.info(f"✅ update_message_content: Successfully updated message {msg_id}")
                return True
            else:
                logger.error(f"❌ update_message_content: Update returned no data. Result: {result}")
                # This can happen if RLS policy blocks the update or row doesn't exist
                return False
                
        except Exception as e:
            logger.error(f"❌ update_message_content failed with exception: {e}", exc_info=True)
            return False
    
    async def get_message_by_id(self, message_id: UUID, user: User) -> Optional[Message]:
        """Fetch a specific message by ID"""
        try:
            msg_id = str(message_id)
            uid = str(user.id)
            result = await async_db_execute(
                lambda: self.db.table("messages").select("*")
                .eq("id", msg_id).eq("user_id", uid).execute()
            )
            if not result.data:
                return None
            
            record = result.data[0]
            return Message(
                id=record["id"],
                conversation_id=record["conversation_id"],
                user_id=record["user_id"],
                role=record["role"],
                content=record["content"],
                metadata=record.get("metadata", {}),
                parent_id=record.get("parent_id"),
                created_at=record["created_at"]
            )
        except Exception as e:
            logger.error(f"get_message_by_id failed: {e}")
            return None

    async def get_conversation_messages(self, conversation_id: UUID, user: User, limit: Optional[int] = None) -> List[Message]:
        """Get messages for a conversation, translating if needed"""
        start = time.time()
        try:
            conv_id = str(conversation_id)
            uid = str(user.id)
            
            def _query():
                q = self.db.table("messages").select("*")\
                    .eq("conversation_id", conv_id)\
                    .eq("user_id", uid)\
                    .order("created_at")
                if limit:
                    q = q.limit(limit)
                return q.execute()
            
            result = await async_db_execute(_query)
            
            all_messages = []
            msg_by_id = {}
            parent_ids = set()
            
            for r in result.data or []:
                try:
                    msg_obj = Message(
                        id=r["id"],
                        conversation_id=r["conversation_id"],
                        role=r["role"],
                        content=r["content"],
                        metadata=r.get("metadata", {}),
                        parent_id=r.get("parent_id"),
                        translations=r.get("translations") or {},
                        created_at=r["created_at"]
                    )
                    all_messages.append(msg_obj)
                except Exception as e:
                    logger.error(f"Failed to create Message object: {e} | Data keys: {list(r.keys()) if r else 'None'}")
                    
            # Rebuild lookup maps and leaves for threaded DAG traversal
            msg_by_id = {m.id: m for m in all_messages}
            parent_ids = {m.parent_id for m in all_messages if m.parent_id}
            
            # Resolve the active thread by finding the leaf node with the latest created_at
            leaves = [m for m in all_messages if m.id not in parent_ids]
            if not leaves:
                messages = all_messages
            else:
                latest_leaf = max(leaves, key=lambda m: m.created_at)
                thread = []
                curr = latest_leaf
                while curr:
                    thread.append(curr)
                    if not curr.parent_id:
                        break
                    curr = msg_by_id.get(curr.parent_id)
                messages = thread[::-1]
            
            if limit:
                messages = messages[-limit:]
            
            # --- TRANSLATION LOGIC ---
            from app.services.translation import translation_service
            
            target_lang = getattr(user, 'language', 'en')
            messages_needing_translation = []
            
            for msg_obj in messages:
                # Check if translation needed (skip images)
                is_image = "![" in msg_obj.content
                if not is_image and (not msg_obj.translations or target_lang not in msg_obj.translations):
                    messages_needing_translation.append(msg_obj)
            
            # Run translations — cap batch to avoid blocking (P1 #7)
            if messages_needing_translation:
                batch = messages_needing_translation[:MAX_INLINE_TRANSLATIONS]
                logger.info(f"Translating {len(batch)}/{len(messages_needing_translation)} messages to {target_lang}")
                
                async def translate_and_update(msg):
                    try:
                        translated_text = await translation_service.translate_text(msg.content, target_lang)
                        if translated_text:
                            if not msg.translations: msg.translations = {}
                            msg.translations[target_lang] = translated_text
                            
                            msg_id = str(msg.id)
                            translations = msg.translations
                            await async_db_execute(
                                lambda: self.db.table("messages").update({
                                    "translations": translations
                                }).eq("id", msg_id).execute()
                            )
                    except Exception as e:
                        logger.warning(f"Translation task error: {e}")
                
                translation_tasks = [translate_and_update(m) for m in batch]
                try:
                    await asyncio.gather(*translation_tasks)
                except Exception as e:
                    logger.error(f"Translation gather error: {e}")
                
                # Fire-and-forget remaining translations in background
                remaining = messages_needing_translation[MAX_INLINE_TRANSLATIONS:]
                if remaining:
                    async def translate_remaining():
                        for m in remaining:
                            await translate_and_update(m)
                    asyncio.create_task(translate_remaining())

            logger.debug(f"get_conversation_messages: {(time.time()-start)*1000:.0f}ms, count={len(messages)}")
            return messages
            
        except Exception as e:
            logger.error(f"get_conversation_messages failed: {e}")
            return []
    
    async def get_recent_messages(self, conversation_id: UUID, user: User, limit: int = 20) -> List[Message]:
        """Get recent messages for AI context"""
        start = time.time()
        try:
            conv_id = str(conversation_id)
            uid = str(user.id)
            result = await async_db_execute(
                lambda: self.db.table("messages").select("*")\
                    .eq("conversation_id", conv_id)\
                    .eq("user_id", uid)\
                    .order("created_at", desc=True)\
                    .limit(limit)\
                    .execute()
            )

            # --- FETCH ASSISTANT RESPONSES ---
            # 1. Collect all user_message_ids
            user_msg_ids = [str(r["id"]) for r in result.data or []]
            
            messages = []
            if user_msg_ids:
                resp_result = await async_db_execute(
                    lambda: self.db.table("assistant_responses").select("*")\
                        .in_("user_message_id", user_msg_ids)\
                        .eq("is_active", True)\
                        .execute()
                )
                
                if resp_result.data:
                    active_responses = {r["user_message_id"]: r for r in resp_result.data}
                    
                    stitched_messages = []
                    for r in result.data:
                        # Append the user message
                        stitched_messages.append(Message(
                            id=r["id"],
                            conversation_id=r["conversation_id"],
                            user_id=r["user_id"],
                            role=r["role"],
                            content=r["content"],
                            metadata=r.get("metadata", {}),
                            parent_id=r.get("parent_id"),
                            created_at=r["created_at"]
                        ))
                        
                        # Append the active assistant response if it exists
                        has_active_response = active_responses.get(str(r["id"]))
                        if has_active_response and r["role"] == 'user':
                            assistant_msg = Message(
                                id=has_active_response["id"],
                                conversation_id=r["conversation_id"],
                                role="assistant",
                                content=has_active_response["content"],
                                metadata=has_active_response.get("metadata", {}),
                                parent_id=r["id"],
                                created_at=has_active_response["created_at"]
                            )
                            stitched_messages.append(assistant_msg)
                            
                    messages = stitched_messages
            
            if not messages:
                for r in result.data or []:
                    messages.append(Message(
                        id=r["id"],
                        conversation_id=r["conversation_id"],
                        user_id=r["user_id"],
                        role=r["role"],
                        content=r["content"],
                        metadata=r.get("metadata", {}),
                        parent_id=r.get("parent_id"),
                        created_at=r["created_at"]
                    ))

            # Reverse to get chronological order
            messages.reverse()
            
            logger.debug(f"get_recent_messages: {(time.time()-start)*1000:.0f}ms, count={len(messages)}")
            return messages
            
        except Exception as e:
            logger.error(f"get_recent_messages failed: {e}")
            return []

    async def get_message_thread(self, leaf_message_id: UUID, user: User, max_depth: int = 100, include_children: bool = False) -> List[Message]:
        """Walk the DAG from a leaf message back to root via parent_id chain.
        Returns messages in chronological order (root first, leaf last).
        If include_children is True, fetches descendants by traversing the latest child at each step.
        """
        start = time.time()
        
        try:
            leaf_id = str(leaf_message_id)
            uid = str(user.id)
            leaf_result = await async_db_execute(
                lambda: self.db.table("messages").select("conversation_id")\
                    .eq("id", leaf_id)\
                    .eq("user_id", uid)\
                    .execute()
            )
            
            if not leaf_result.data:
                return []
            
            conv_id = leaf_result.data[0]["conversation_id"]
            
            # Fetch ALL messages for this conversation matching the leaf node timeline
            # We ONLY need id, parent_id, role, content, metadata, created_at, avoiding massive blobs if possible later
            all_result = await async_db_execute(
                lambda: self.db.table("messages").select("id, conversation_id, role, content, metadata, parent_id, created_at")\
                    .eq("conversation_id", conv_id)\
                    .eq("user_id", uid)\
                    .execute()
            )
            
            if not all_result.data:
                return []
            
            thread = []
            current_id = str(leaf_message_id)
            all_messages = [r for r in all_result.data]
            msg_map = {r["id"]: r for r in all_messages}
            
            # --- WALK UPWARD ---
            for _ in range(max_depth):
                r = msg_map.get(current_id)
                if not r:
                    break
                
                msg = Message(
                    id=r["id"],
                    conversation_id=r["conversation_id"],
                    role=r["role"],
                    content=r["content"],
                    metadata=r.get("metadata", {}),
                    parent_id=r.get("parent_id"),
                    created_at=r["created_at"]
                )
                thread.append(msg)
                
                if not r.get("parent_id"):
                    break  # Reached root
                current_id = r["parent_id"]
            
            thread.reverse()  # Root first, leaf last
            
            # --- WALK DOWNWARD ---
            if include_children:
                children_map = {}
                for m in all_messages:
                    pid = m.get("parent_id")
                    if pid:
                        if pid not in children_map:
                            children_map[pid] = []
                        children_map[pid].append(m)
                
                # Helper function for extracting timestamps, moved here to prep for chronological fallback
                def get_created_at_timestamp(child):
                    created_at = child["created_at"]
                    if isinstance(created_at, str):
                        # Parse ISO format string to datetime for proper comparison
                        from datetime import datetime
                        try:
                            return datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            # Fallback to string comparison if parsing fails
                            return created_at
                    return created_at

                current_id = str(leaf_message_id)
                
                for _ in range(max_depth):
                    children = children_map.get(current_id, [])
                    if not children:
                        break  # Leaf reached — no stitching needed
                    
                    # Pick the active child (latest created_at)
                    latest_child = max(children, key=get_created_at_timestamp)
                    child_msg = Message(
                        id=latest_child["id"],
                        conversation_id=latest_child["conversation_id"],
                        role=latest_child["role"],
                        content=latest_child["content"],
                        metadata=latest_child.get("metadata", {}),
                        parent_id=latest_child.get("parent_id"),
                        created_at=latest_child["created_at"]
                    )
                    thread.append(child_msg)
                    current_id = str(latest_child["id"])

            # --- FETCH ASSISTANT RESPONSES ---
            # 1. Collect all user_message_ids in the thread
            user_msg_ids = [str(m.id) for m in thread if m.role == 'user']
            
            # 2. Fetch their active branch responses
            if user_msg_ids:
                resp_result = await async_db_execute(
                    lambda: self.db.table("assistant_responses").select("*")\
                        .in_("user_message_id", user_msg_ids)\
                        .eq("is_active", True)\
                        .execute()
                )
                
                if resp_result.data:
                    # Map response by user_message_id
                    active_responses = {r["user_message_id"]: r for r in resp_result.data}
                    
                    # 3. Interleave them
                    stitched_thread = []
                    for msg in thread:
                        stitched_thread.append(msg)
                        has_active_response = active_responses.get(str(msg.id))
                        if has_active_response and msg.role == 'user':
                            assistant_msg = Message(
                                id=has_active_response["id"],
                                conversation_id=msg.conversation_id,
                                role="assistant",
                                content=has_active_response["content"],
                                metadata=has_active_response.get("metadata", {}),
                                parent_id=msg.id,
                                created_at=has_active_response["created_at"]
                            )
                            stitched_thread.append(assistant_msg)
                            
                    thread = stitched_thread

            logger.debug(f"get_message_thread: {(time.time()-start)*1000:.0f}ms, depth={len(thread)}")
            return thread
            
        except Exception as e:
            logger.error(f"get_message_thread failed: {e}")
            return []

    async def get_branched_messages(self, conversation_id: UUID, user: User) -> Dict[str, Any]:
        """
        Get all messages for a conversation, including all assistant responses (branches)
        and the currently active branch selections.
        """
        start = time.time()
        try:
            conv_id = str(conversation_id)
            uid = str(user.id)
            
            # 1. Get user messages
            msg_result = await async_db_execute(
                lambda: self.db.table("messages").select("*")\
                    .eq("conversation_id", conv_id)\
                    .eq("user_id", uid)\
                    .order("created_at")\
                    .execute()
            )
            
            messages = []
            for r in msg_result.data or []:
                messages.append(Message(
                    id=r["id"],
                    conversation_id=r["conversation_id"],
                    role=r["role"],
                    content=r["content"],
                    metadata=r.get("metadata", {}),
                    parent_id=r.get("parent_id"),
                    created_at=r["created_at"]
                ))
                
            # 2. Get assistant responses
            # We need all responses for all messages in this conversation
            # Since responses are tied to user_message_id, we can join or query directly
            # For simplicity, we query all responses where user_message_id is in our messages list
            msg_ids = [str(m.id) for m in messages if m.role == 'user']
            
            responses = []
            if msg_ids:
                # Supabase Python client 'in_' filter expects a list
                resp_result = await async_db_execute(
                    lambda: self.db.table("assistant_responses").select("*")\
                        .in_("user_message_id", msg_ids)\
                        .execute()
                )
                
                from app.models.conversation import AssistantResponse
                for r in resp_result.data or []:
                    responses.append(AssistantResponse(
                        id=r["id"],
                        user_message_id=r["user_message_id"],
                        branch_label=r["branch_label"],
                        content=r["content"],
                        model_used=r.get("model_used"),
                        token_count=r.get("token_count"),
                        metadata=r.get("metadata", {}),
                        is_active=r.get("is_active", True),
                        created_at=r["created_at"],
                        updated_at=r["updated_at"]
                    ))
                    
            # 3. Get branch selections
            sel_result = await async_db_execute(
                lambda: self.db.table("branch_selections").select("*")\
                    .eq("conversation_id", conv_id)\
                    .execute()
            )
            
            from app.models.conversation import BranchSelection
            selections = []
            for r in sel_result.data or []:
                selections.append(BranchSelection(
                    id=r["id"],
                    conversation_id=r["conversation_id"],
                    user_message_id=r["user_message_id"],
                    active_response_id=r.get("active_response_id"),
                    updated_at=r["updated_at"]
                ))
                
            logger.debug(f"get_branched_messages: {(time.time()-start)*1000:.0f}ms")
            
            return {
                "messages": messages,
                "responses": responses,
                "selections": selections
            }
            
        except Exception as e:
            logger.error(f"get_branched_messages failed: {e}")
            raise
            
    async def create_response_branch(self, user_message_id: UUID, content: str, model_used: str = None, token_count: int = None, metadata: dict = None) -> Any:
        """Create a new assistant response branch for a user message"""
        try:
            msg_id = str(user_message_id)
            
            # Verify the message exists
            msg_check = await async_db_execute(
                lambda: self.db.table("messages").select("conversation_id").eq("id", msg_id).execute()
            )
            
            if not msg_check.data:
                logger.error(f"create_response_branch: msg {msg_id} not found")
                return None
                
            conv_id = msg_check.data[0]["conversation_id"]
            
            # Determine the next branch label logically (A, B, C...)
            existing_responses = await async_db_execute(
                lambda: self.db.table("assistant_responses").select("branch_label")\
                    .eq("user_message_id", msg_id)\
                    .execute()
            )
            
            branch_count = len(existing_responses.data) if existing_responses.data else 0
            # A=65, B=66, etc.
            next_label = chr(65 + min(branch_count, 25))
            
            # Insert the new response
            data = {
                "user_message_id": msg_id,
                "branch_label": next_label,
                "content": content,
                "model_used": model_used,
                "token_count": token_count,
                "metadata": metadata or {}
            }
            
            result = await async_db_execute(
                lambda: self.db.table("assistant_responses").insert(data).execute()
            )
            
            if not result.data:
                return None
                
            response_record = result.data[0]
            new_response_id = response_record["id"]
            
            # Auto-select this new branch
            await self.set_active_branch(conv_id, msg_id, new_response_id)
            
            from app.models.conversation import AssistantResponse
            return AssistantResponse(
                id=response_record["id"],
                user_message_id=response_record["user_message_id"],
                branch_label=response_record["branch_label"],
                content=response_record["content"],
                model_used=response_record.get("model_used"),
                token_count=response_record.get("token_count"),
                metadata=response_record.get("metadata", {}),
                is_active=response_record.get("is_active", True),
                created_at=response_record["created_at"],
                updated_at=response_record["updated_at"]
            )
            
        except Exception as e:
            logger.error(f"create_response_branch failed: {e}")
            raise
            
    async def set_active_branch(self, conversation_id: str, user_message_id: str, response_id: str) -> bool:
        """Set the active response branch for a user message"""
        try:
            logger.info(f"🔀 set_active_branch: conv={conversation_id}, user_msg={user_message_id}, response={response_id}")
            
            # Upsert into branch_selections (uses UNIQUE constraint on conversation_id, user_message_id)
            data = {
                "conversation_id": str(conversation_id),
                "user_message_id": str(user_message_id),
                "active_response_id": str(response_id)
            }

            # First try to check if record exists
            check_result = await async_db_execute(
                lambda: self.db.table("branch_selections").select("id")\
                    .eq("conversation_id", str(conversation_id))\
                    .eq("user_message_id", str(user_message_id))\
                    .execute()
            )
            
            if check_result.data and len(check_result.data) > 0:
                # Update existing record
                logger.info(f"📝 Updating existing branch selection")
                result = await async_db_execute(
                    lambda: self.db.table("branch_selections").update(
                        {"active_response_id": str(response_id)}
                    ).eq("conversation_id", str(conversation_id))\
                     .eq("user_message_id", str(user_message_id))\
                     .execute()
                )
            else:
                # Insert new record
                logger.info(f"➕ Inserting new branch selection")
                result = await async_db_execute(
                    lambda: self.db.table("branch_selections").insert(data).execute()
                )

            logger.info(f"✅ set_active_branch completed: {bool(result.data)}")
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"❌ set_active_branch failed: {e}", exc_info=True)
            return False
            
    async def delete_response_branch(self, response_id: UUID) -> bool:
        """Delete an assistant response branch"""
        try:
            resp_id = str(response_id)
            
            result = await async_db_execute(
                lambda: self.db.table("assistant_responses").delete().eq("id", resp_id).execute()
            )
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"delete_response_branch failed: {e}")
            return False

    async def get_branches(self, message_id: UUID, user: User) -> List[Message]:
        """[DEPRECATED] Get all sibling messages (messages sharing the same parent_id)."""
        try:
            msg_id = str(message_id)
            uid = str(user.id)
            
            # First get the target message's parent_id
            result = await async_db_execute(
                lambda: self.db.table("messages").select("parent_id")\
                    .eq("id", msg_id)\
                    .eq("user_id", uid)\
                    .execute()
            )
            
            if not result.data:
                return []
            
            parent_id = result.data[0].get("parent_id")
            if not parent_id:
                return []  # Root message has no siblings
            
            # Get all messages with the same parent_id
            siblings = await async_db_execute(
                lambda: self.db.table("messages").select("*")\
                    .eq("parent_id", parent_id)\
                    .eq("user_id", uid)\
                    .order("created_at")\
                    .execute()
            )
            
            return [
                Message(
                    id=r["id"],
                    conversation_id=r["conversation_id"],
                    role=r["role"],
                    content=r["content"],
                    metadata=r.get("metadata", {}),
                    parent_id=r.get("parent_id"),
                    created_at=r["created_at"]
                )
                for r in siblings.data or []
            ]
            
        except Exception as e:
            logger.error(f"get_branches failed: {e}")
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
            conv_id = str(conversation_id)
            ts = datetime.utcnow().isoformat()
            await async_db_execute(
                lambda: self.db.table("conversations").update({
                    "updated_at": ts
                }).eq("id", conv_id).execute()
            )
        except Exception:
            pass