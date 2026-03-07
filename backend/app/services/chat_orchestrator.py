import time
import json
import asyncio
import logging
from typing import Dict, Any, AsyncGenerator, Optional
from fastapi import BackgroundTasks

from app.models.user import User
from app.models.conversation import MessageCreate
from app.core.container import container
from app.services.postprocessing import mermaid_processor
from app.security import LLMSecurityGuard, get_hardened_prompt

logger = logging.getLogger(__name__)
security_guard = LLMSecurityGuard()

class ChatOrchestratorService:
    """
    Orchestrates the entire chat sequence including:
    - Security checks and prompt injection detection
    - Vision model contextualization for images
    - RAG context assembly
    - AI Model execution & stream generation
    - Persistent database state management
    
    Uses ServiceContainer for all dependencies - NO direct instantiation.
    """

    def __init__(self, db=None):
        """Initialize with container - lazy loading for efficiency"""
        self._container = None
        self._db = db
    
    @property
    def container(self):
        """Get container - should be initialized at app startup"""
        if self._container is None:
            # Don't try to initialize - should already be initialized at app startup
            self._container = container
        return self._container
    
    @property
    def ai(self):
        """Get AI service from container"""
        return self.container.get('ai_service')
    
    @property
    def chat(self):
        """Get chat service from container"""
        return self.container.get('chat_service')
    
    @property
    def rag(self):
        """Get RAG service from container"""
        return self.container.get('rag_service')
    
    @property
    def mermaid(self):
        """Get centralized Mermaid processor"""
        return mermaid_processor

    async def process_chat_request(self, chat_request, current_user: User) -> dict:
        """Process a synchronous chat request"""
        security_guard.validate_transaction(chat_request.message)

        injection_check = self.ai.check_for_injection(chat_request.message)
        if injection_check["is_injection"]:
            user_msg = MessageCreate(conversation_id=chat_request.conversation_id, role="user", content=chat_request.message, metadata=chat_request.metadata)
            await self.chat.add_message(user_msg, current_user)
            refusal_msg = MessageCreate(conversation_id=chat_request.conversation_id, role="assistant", content=injection_check["refusal_message"], metadata={"security_refusal": True})
            await self.chat.add_message(refusal_msg, current_user)
            return {"response": injection_check["refusal_message"], "context_used": False}

        user_message = MessageCreate(
            conversation_id=chat_request.conversation_id,
            role="user",
            content=chat_request.message,
            metadata=chat_request.metadata,
            parent_id=chat_request.parent_id
        )
        saved_msg = await self.chat.add_message(user_message, current_user)

        images = chat_request.metadata.get("images", [])
        if images:
            image_analyses = []
            for img_url in images:
                analysis = await self.ai.analyze_image(img_url)
                image_analyses.append(f"--- IMAGE ANALYSIS ---\n{analysis}\n----------------------")
            if image_analyses:
                chat_request.message += "\n\n[SYSTEM: The user uploaded images.]\n\n" + "\n\n".join(image_analyses)

        hardened_message = get_hardened_prompt(chat_request.message)
        ai_response = await self.ai.generate_response(
            message=hardened_message,
            conversation_id=chat_request.conversation_id,
            user=current_user,
            mode=chat_request.mode,
            use_rag=chat_request.use_rag
        )

        try:
            security_guard.validate_transaction(prompt=chat_request.message, response=ai_response)
        except Exception as e:
            logger.error(f"Output security violation: {e}")
            ai_response = "I apologize, but I cannot provide that response as it may violate safety guidelines."

        # Apply Mermaid fixes before saving to DB
        ai_response = self.mermaid.fix_markdown_mermaid(ai_response)[0]

        branch_response = await self.chat.create_response_branch(
            user_message_id=saved_msg.id if saved_msg else None,
            content=ai_response,
            model_used="sync",
            token_count=len(ai_response) // 4,
            metadata={"mode": chat_request.mode, "rag_used": chat_request.use_rag, "source_language": chat_request.language}
        )

        return {"response": ai_response, "context_used": chat_request.use_rag}


    async def stream_chat_request(self, chat_request, current_user: User, background_tasks: BackgroundTasks) -> AsyncGenerator[str, None]:
        """Process a streaming chat request"""
        original_message = chat_request.message.strip()
        effective_mode = chat_request.mode

        if original_message.lower().startswith("deep research:"):
            effective_mode = "deep_research"
            chat_request.message = original_message[14:].strip()

        chat_request.mode = effective_mode

        # 1. Vision Analysis
        image_context_str = ""
        images = chat_request.metadata.get("images", [])
        attachments = chat_request.metadata.get("attachments", [])

        if images:
            image_analyses = []
            for i, img_url in enumerate(images):
                analysis = await self.ai.analyze_image(img_url)
                image_analyses.append(f"--- IMAGE ANALYSIS (Image {i+1}) ---\n{analysis}\n----------------------")
                await self.rag.store_text_as_memory(
                    text=f"Visual Content Analysis of Uploaded Image {i+1}:\n{analysis}",
                    conversation_id=chat_request.conversation_id, user_id=current_user.id,
                    source=f"image_upload_{int(time.time())}_{i}.jpg", metadata={"type": "image_analysis", "original_url": img_url}
                )
            if image_analyses:
                image_context_str = "\n\n[SYSTEM: The user uploaded images.]\n\n" + "\n\n".join(image_analyses)

        elif attachments:
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
            image_attachments = [a for a in attachments if any(a.get('name', '').lower().endswith(ext) for ext in image_extensions)]
            if image_attachments:
                stored_analyses = await self.rag.get_recent_image_analyses(
                    conversation_id=chat_request.conversation_id, filenames=[a['name'] for a in image_attachments]
                )
                if stored_analyses:
                    image_context_str = "\n\n[SYSTEM: The user uploaded images.]\n\n" + stored_analyses

        # 2. Injection Check
        injection_check = self.ai.check_for_injection(chat_request.message)
        if injection_check["is_injection"]:
            user_msg = MessageCreate(conversation_id=chat_request.conversation_id, role="user", content=chat_request.message, metadata=chat_request.metadata)
            await self.chat.add_message(user_msg, current_user)
            refusal_msg = MessageCreate(conversation_id=chat_request.conversation_id, role="assistant", content=injection_check["refusal_message"], metadata={"security_refusal": True})
            await self.chat.add_message(refusal_msg, current_user)

            refusal_chunk = json.dumps({"text": injection_check["refusal_message"]})
            yield f"data: {refusal_chunk}\n\n"
            yield "data: [DONE]\n\n"
            return

        # 3. Save User Message (or reuse existing one for regeneration)
        auto_parent_id = chat_request.parent_id
        
        saved_msg = None
        if hasattr(chat_request, 'user_message_id') and chat_request.user_message_id:
            logger.debug(f"Branch regeneration requested for user message: {chat_request.user_message_id}")
            saved_msg = await self.chat.get_message_by_id(chat_request.user_message_id, current_user)
            if not saved_msg:
                logger.error(f"User message {chat_request.user_message_id} not found for regeneration. Creating new.")
                
        if not saved_msg:
            user_message = MessageCreate(
                conversation_id=chat_request.conversation_id,
                role="user",
                content=chat_request.message,
                metadata=chat_request.metadata,
                parent_id=auto_parent_id
            )
            saved_msg = await self.chat.add_message(user_message, current_user)

        # We no longer pre-create an assistant message in the `messages` table.
        # Instead, we will create an `AssistantResponse` branch when the stream completes.

        # 4. Background Processor
        async def post_stream_processing(response_text: str, is_final: bool):
            if not is_final or not response_text or not saved_msg:
                return
            try:
                # Apply Mermaid fixes before saving to DB
                response_text = self.mermaid.fix_markdown_mermaid(response_text)[0]
                
                # Create the branch in assistant_responses instead of messages
                branch_response = await self.chat.create_response_branch(
                    user_message_id=saved_msg.id,
                    content=response_text,
                    model_used="stream",  # Ideally we extract this from AI provider
                    token_count=len(response_text) // 4,  # Rough estimate
                    metadata={"mode": chat_request.mode, "rag_used": chat_request.use_rag, "source_language": chat_request.language}
                )
                
                # Optional: Queue translation for the branch content if needed
                # translation_service = TranslationService(self.ai.db)
                # await translation_service.queue_message_translation(...)
                
            except Exception as bg_err:
                logger.error(f"Post-stream error creating branch: {bg_err}")

        # 5. Core Generator Loop
        full_response = ""
        is_complete = False
        try:
            # Send initial metadata chunk with the USER ID
            if saved_msg:
                meta_data = {
                    "type": "meta",
                    "user_message_id": str(saved_msg.id),
                    "is_branching": True
                }
                yield f"data: {json.dumps(meta_data)}\n\n"

            async for chunk in self.ai.generate_streaming_response(
                message=chat_request.message,
                conversation_id=chat_request.conversation_id,
                user=current_user,
                mode=chat_request.mode,
                use_rag=chat_request.use_rag,
                additional_context=image_context_str,
                language_override=chat_request.language,
                context_parent_id=saved_msg.id if saved_msg else None,
                metadata=chat_request.metadata  # Pass metadata for image attachments
            ):
                if isinstance(chunk, dict):
                    encoded = json.dumps(chunk)
                    yield f"data: {encoded}\n\n"
                else:
                    full_response += chunk
                    # json.dumps securely handles escaping newlines.
                    yield f"data: {json.dumps({'text': chunk})}\n\n"
                await asyncio.sleep(0)

            is_complete = True
            yield "data: [DONE]\n\n"
            background_tasks.add_task(post_stream_processing, full_response, is_complete)

        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_text = f"\n\n[System Error: {str(e)}]"
            error_chunk = json.dumps({"text": error_text})
            yield f"data: {error_chunk}\n\n"
