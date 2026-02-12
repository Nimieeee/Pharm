"""
AI Chat API endpoints
"""

from typing import Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import Client

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.ai import AIService
from app.services.chat import ChatService
from app.services.enhanced_rag import EnhancedRAGService
from app.services.deep_research import DeepResearchService
from app.services.image_gen import ImageGenerationService
from app.services.translation_service import TranslationService
from app.models.user import User
from app.models.conversation import MessageCreate
from app.models.document import DocumentUploadResponse, DocumentSearchRequest, DocumentSearchResponse
from app.security import LLMSecurityGuard, SecurityViolationException, get_hardened_prompt
import logging
import json
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize security guard (singleton)
security_guard = LLMSecurityGuard()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: UUID
    mode: str = "detailed"  # "fast" or "detailed"
    use_rag: bool = True
    metadata: Dict[str, Any] = {}
    language: str = "en"  # Language for AI response


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    conversation_id: UUID
    mode: str
    context_used: bool


def get_ai_service(db: Client = Depends(get_db)) -> AIService:
    """Get AI service"""
    return AIService(db)


def get_chat_service(db: Client = Depends(get_db)) -> ChatService:
    """Get chat service"""
    return ChatService(db)


def get_rag_service(db: Client = Depends(get_db)) -> EnhancedRAGService:
    """Get enhanced RAG service"""
    return EnhancedRAGService(db)


def get_deep_research_service(db: Client = Depends(get_db)) -> DeepResearchService:
    """Get deep research service"""
    return DeepResearchService(db)


def get_image_gen_service() -> ImageGenerationService:
    """Get image generation service"""
    return ImageGenerationService()


class ImageGenerationRequest(BaseModel):
    """Image generation request model"""
    prompt: str
    conversation_id: UUID


@router.post("/image-generation")
async def generate_image(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_user),
    image_service: ImageGenerationService = Depends(get_image_gen_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Generate an image based on a prompt
    """
    print(f"🎨 Image Generation requested by user {current_user.id}")
    print(f"📝 Prompt: {request.prompt}")
    
    try:
        logger.info(f"Generating image for user {current_user.id} with prompt: {request.prompt}")
        
        # Call the image generation service
        result = await image_service.generate_image(request.prompt)
        
        # Save the interaction to chat history
        # 1. Save user prompt
        await chat_service.add_message(
            MessageCreate(
                conversation_id=request.conversation_id,
                content=f"/image {request.prompt}",
                role="user"
            ),
            current_user
        )
        
        # 2. Save assistant response (image URL)
        assistant_message = result.get("content", "")
        if not assistant_message:
             assistant_message = "Failed to generate image content."
             
        await chat_service.add_message(
            MessageCreate(
                conversation_id=request.conversation_id,
                content=assistant_message,
                role="assistant"
            ),
            current_user
        )
        
        return {
            "status": "success",
            "image_url": assistant_message,
            "markdown": assistant_message
        }
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Generate AI response for a chat message
    
    - **message**: User message
    - **conversation_id**: Conversation ID
    - **mode**: Response mode ("fast" or "detailed")
    - **use_rag**: Whether to use document context
    """
    try:
        print(f"💬 Chat endpoint called by user {current_user.id}")
        print(f"📝 Message: {chat_request.message[:100]}...")
        print(f"🆔 Conversation ID: {chat_request.conversation_id}")
        print(f"⚙️ Mode: {chat_request.mode}, RAG: {chat_request.use_rag}")
        
        # Security Layer: Validate input before processing
        print("🔒 Running security checks...")
        try:
            security_guard.validate_transaction(chat_request.message)
            print("✅ Security checks passed")
            
            # 1. Check for Prompt Injection (Pre-Filter)
            injection_check = ai_service.check_for_injection(chat_request.message)
            if injection_check["is_injection"]:
                print(f"🚨 Prompt Injection Detected: {chat_request.message[:50]}...")
                
                # We still need to validate conversation exists to save the refusal
                conversation = await chat_service.get_conversation(
                    chat_request.conversation_id, current_user
                )
                if not conversation:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Conversation not found"
                    )
                
                # Save user message and refusal
                user_msg = MessageCreate(
                    conversation_id=chat_request.conversation_id,
                    role="user",
                    content=chat_request.message,
                    metadata=chat_request.metadata
                )
                await chat_service.add_message(user_msg, current_user)
                
                refusal_msg = MessageCreate(
                    conversation_id=chat_request.conversation_id,
                    role="assistant",
                    content=injection_check["refusal_message"],
                    metadata={"security_refusal": True}
                )
                await chat_service.add_message(refusal_msg, current_user)
                
                return ChatResponse(
                    response=injection_check["refusal_message"],
                    conversation_id=chat_request.conversation_id,
                    mode=chat_request.mode,
                    context_used=False
                )
                
        except SecurityViolationException as e:
            logger.warning(f"🚨 Security violation blocked: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.to_dict()
            )
        
        # Validate conversation belongs to user
        print("🔍 Validating conversation...")
        conversation = await chat_service.get_conversation(
            chat_request.conversation_id, current_user
        )
        if not conversation:
            print("❌ Conversation not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        print("✅ Conversation validated")
        
        # Add user message to conversation
        print("💾 Adding user message to database...")
        user_message = MessageCreate(
            conversation_id=chat_request.conversation_id,
            role="user",
            content=chat_request.message,
            metadata=chat_request.metadata
        )
        
        await chat_service.add_message(user_message, current_user)
        print("✅ User message added")
        
        # Check for images in metadata and process them (Vision-to-Text Bridge)
        images = chat_request.metadata.get("images", [])
        if images:
            print(f"🖼️ Processing {len(images)} images with Vision Model...")
            image_analyses = []
            for img_url in images:
                # Call Pixtral via AI Service
                analysis = await ai_service.analyze_image(img_url)
                image_analyses.append(f"--- IMAGE ANALYSIS ---\n{analysis}\n----------------------")
            
            # Append analysis to message context for the main model
            if image_analyses:
                chat_request.message += "\n\n[SYSTEM: The user uploaded images. Here is the detailed analysis of their content generated by the vision model. Use this information to answer the user's request.]\n\n" + "\n\n".join(image_analyses)
                print("✅ Image analysis appended to context")
        
        # Generate AI response with hardened prompt
        print("🤖 Calling AI service...")
        # Use hardened system prompt template
        hardened_message = get_hardened_prompt(chat_request.message)
        
        ai_response = await ai_service.generate_response(
            message=hardened_message,
            conversation_id=chat_request.conversation_id,
            user=current_user,
            mode=chat_request.mode,
            use_rag=chat_request.use_rag
        )
        print(f"✅ AI response generated: {len(ai_response)} chars")
        
        # Security Layer: Audit output
        print("🔒 Auditing AI response...")
        try:
            security_guard.validate_transaction(
                prompt=chat_request.message,
                response=ai_response
            )
            print("✅ Output audit passed")
        except SecurityViolationException as e:
            logger.error(f"🚨 Output security violation: {e}")
            # Return a safe error message instead of the potentially compromised response
            ai_response = "I apologize, but I cannot provide that response as it may violate safety guidelines. Please rephrase your question."
        
        # Add AI response to conversation
        print("💾 Adding AI response to database...")
        assistant_message = MessageCreate(
            conversation_id=chat_request.conversation_id,
            role="assistant",
            content=ai_response,
            metadata={
                "mode": chat_request.mode,
                "rag_used": chat_request.use_rag
            }
        )
        
        await chat_service.add_message(assistant_message, current_user)
        print("✅ AI response added")
        
        print("🎉 Chat endpoint completed successfully")
        return ChatResponse(
            response=ai_response,
            conversation_id=chat_request.conversation_id,
            mode=chat_request.mode,
            context_used=chat_request.use_rag
        )
        
    except HTTPException as e:
        print(f"❌ HTTP Exception in chat endpoint: {e.detail}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error in chat endpoint: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Generate streaming AI response for a chat message
    
    Returns Server-Sent Events (SSE) stream
    """
    import time
    start = time.time()
    print(f"🚀 POST /chat/stream - conv={chat_request.conversation_id}, user={current_user.id}")
    print(f"📝 Message: {chat_request.message[:100]}...")
    
    try:
        # Validate conversation belongs to user
        conv_start = time.time()
        conversation = await chat_service.get_conversation(
            chat_request.conversation_id, current_user
        )
        print(f"  ⏱️ Conversation check: {(time.time() - conv_start)*1000:.0f}ms")
        
        if not conversation:
            print(f"❌ Conversation not found!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        # =====================================================================
        # 0. VISION ANALYSIS - Handle both direct images AND uploaded attachments
        # =====================================================================
        image_context_str = ""
        images = chat_request.metadata.get("images", [])
        attachments = chat_request.metadata.get("attachments", [])
        
        # DEBUG: Log metadata to understand what's being received
        print(f"📋 DEBUG metadata: {chat_request.metadata}")
        print(f"📋 DEBUG images: {images}, attachments: {attachments}")
        
        # Initialize RAG service for image analysis operations
        from app.services.enhanced_rag import EnhancedRAGService
        rag_service = EnhancedRAGService(ai_service.db)
        
        # Case 1: Direct image URLs provided (analyze at chat time)
        if images:
            print(f"🖼️ Processing {len(images)} direct images: Analysis + Embedding...")
            image_analyses = []
            
            for i, img_url in enumerate(images):
                # 1. Vision Analysis
                analysis = await ai_service.analyze_image(img_url)
                formatted_analysis = f"--- IMAGE ANALYSIS (Image {i+1}) ---\n{analysis}\n----------------------"
                image_analyses.append(formatted_analysis)
                
                # 2. Embed & Store in Vector DB (Persistent Memory)
                await rag_service.store_text_as_memory(
                    text=f"Visual Content Analysis of Uploaded Image {i+1}:\n{analysis}",
                    conversation_id=chat_request.conversation_id,
                    user_id=current_user.id,
                    source=f"image_upload_{int(time.time())}_{i}.jpg",
                    metadata={"type": "image_analysis", "original_url": img_url}
                )
            
            if image_analyses:
                image_context_str = "\n\n[SYSTEM: The user uploaded images. Here is the detailed analysis of their content generated by the vision model. Use this information to answer the user's request.]\n\n" + "\n\n".join(image_analyses)
        
        # Case 2: Attachments provided (images already analyzed during upload)
        elif attachments:
            # Check if any attachments are images
            image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
            image_attachments = [a for a in attachments if any(a.get('name', '').lower().endswith(ext) for ext in image_extensions)]
            
            if image_attachments:
                print(f"🖼️ Found {len(image_attachments)} image attachments, fetching stored analyses...")
                
                # Fetch recent image analyses from vector DB for this conversation
                stored_analyses = await rag_service.get_recent_image_analyses(
                    conversation_id=chat_request.conversation_id,
                    filenames=[a['name'] for a in image_attachments]
                )
                
                if stored_analyses:
                    print(f"✅ Retrieved {len(stored_analyses)} chars of image analysis context")
                    image_context_str = "\n\n[SYSTEM: The user uploaded images. Here is the detailed analysis of their content generated by the vision model. Use this information to answer the user's request.]\n\n" + stored_analyses
                else:
                    print(f"⚠️ No stored image analyses found for attachments: {[a['name'] for a in image_attachments]}")


        # 1. Check for Prompt Injection (Pre-Filter)
        injection_check = ai_service.check_for_injection(chat_request.message)
        if injection_check["is_injection"]:
            print(f"🚨 Prompt Injection Detected in Stream: {chat_request.message[:50]}...")
            
            # Save user message and refusal
            user_msg = MessageCreate(
                conversation_id=chat_request.conversation_id,
                role="user",
                content=chat_request.message,
                metadata=chat_request.metadata
            )
            await chat_service.add_message(user_msg, current_user)
            
            refusal_msg = MessageCreate(
                conversation_id=chat_request.conversation_id,
                role="assistant",
                content=injection_check["refusal_message"],
                metadata={"security_refusal": True}
            )
            await chat_service.add_message(refusal_msg, current_user)
            
            # Return streaming refusal
            async def refusal_stream():
                refusal_json = json.dumps({"text": injection_check["refusal_message"]})
                yield f"data: {refusal_json}\n\n"
                yield "data: [DONE]\n\n"
                
            return StreamingResponse(
                refusal_stream(),
                media_type="text/event-stream"
            )
        
        # =====================================================================
        # PREFIX DETECTION: "Lab:" and "Deep Research:"
        # =====================================================================
        original_message = chat_request.message.strip()
        effective_mode = chat_request.mode
        lab_report_mode = False
        
        # Check for "Lab:" prefix → trigger lab report generation
        if original_message.lower().startswith("lab:"):
            lab_report_mode = True
            # Remove prefix and clean up the message
            chat_request.message = original_message[4:].strip()
            logger.info(f"🧪 Lab Report mode triggered via 'Lab:' prefix")
        
        # Check for "Deep Research:" prefix → switch to deep_research mode
        elif original_message.lower().startswith("deep research:"):
            effective_mode = "deep_research"
            chat_request.message = original_message[14:].strip()
            logger.info(f"🔬 Deep Research mode triggered via 'Deep Research:' prefix")
        
        # =====================================================================
        # HANDLE LAB REPORT MODE (Special case - generates structured report)
        # =====================================================================
        if lab_report_mode:
            from app.services.lab_report import LabReportService
            from app.services.enhanced_rag import EnhancedRAGService
            
            # Save user message first
            user_message = MessageCreate(
                conversation_id=chat_request.conversation_id,
                role="user",
                content=original_message,
                metadata=chat_request.metadata
            )
            await chat_service.add_message(user_message, current_user)
            
            async def lab_report_stream():
                try:
                    lab_service = LabReportService()
                    rag_service = EnhancedRAGService(ai_service.supabase)
                    
                    start_msg = json.dumps({'text': '📝 **Generating Lab Report...**\n\n'})
                    yield f"data: {start_msg}\n\n"
                    
                    # Get RAG context for uploaded documents
                    data_context = ""
                    try:
                        context = await rag_service.get_conversation_context(
                            query=chat_request.message,
                            conversation_id=chat_request.conversation_id,
                            user_id=current_user.id,
                            max_chunks=20
                        )
                        if context:
                            data_context = context
                            found_msg = json.dumps({'text': '📄 Found uploaded document context...\n'})
                            yield f"data: {found_msg}\n\n"
                    except Exception as e:
                        logger.warning(f"RAG fetch failed: {e}")
                    
                    analyze_msg = json.dumps({'text': '🔬 Analyzing data and generating sections...\n\n'})
                    yield f"data: {analyze_msg}\n\n"
                    
                    # Generate the lab report
                    full_context = (data_context or "") + "\n" + image_context_str
                    if not full_context.strip():
                        # If no docs and no images, use message itself as context fallback
                        full_context = chat_request.message
                        
                    result = await lab_service.generate_report(
                        experiment_type=chat_request.message,
                        data_context=full_context,
                        methodology="Standard laboratory procedures as described in the provided materials.",
                        user_instructions=None
                    )
                    
                    if result.get("error"):
                        error_msg = result["error"]
                        yield f"data: {json.dumps({'text': f'❌ Error: {error_msg}'})}\n\n"
                    else:
                        # Stream the full report
                        full_report = result.get("full_report", "No report generated")
                        yield f"data: {json.dumps({'text': full_report})}\n\n"
                    
                    # Save assistant message
                    assistant_message = MessageCreate(
                        conversation_id=chat_request.conversation_id,
                        role="assistant",
                        content=result.get("full_report", "Lab report generation completed."),
                        metadata={"mode": "lab_report", "lab_report": True}
                    )
                    await chat_service.add_message(assistant_message, current_user)
                    
                except Exception as e:
                    logger.error(f"Lab report generation failed: {e}")
                    yield f"data: {json.dumps({'text': f'❌ Lab report generation failed: {str(e)}'})}\n\n"
                
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                lab_report_stream(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        
        # Use effective_mode (may have been changed by prefix detection)
        chat_request.mode = effective_mode
        
        # Add user message to conversation
        print(f"💾 Saving user message...")
        msg_start = time.time()
        user_message = MessageCreate(
            conversation_id=chat_request.conversation_id,
            role="user",
            content=chat_request.message,
            metadata=chat_request.metadata
        )
        
        saved_msg = await chat_service.add_message(user_message, current_user)
        print(f"✅ User message saved in {(time.time() - msg_start)*1000:.0f}ms, id={saved_msg.id if saved_msg else 'FAILED'}")
        
        if image_context_str:
            # We pass this as additional_context now, not appending to message
            pass 
        
        # Define background task for saving and translating
        async def post_stream_processing(response_text: str, is_final: bool):
            if not is_final or not response_text:
                return
            
            try:
                print(f"📡 [BG] Saving assistant message for conv {chat_request.conversation_id}...")
                assistant_message = MessageCreate(
                    conversation_id=chat_request.conversation_id,
                    role="assistant",
                    content=response_text,
                    metadata={
                        "mode": chat_request.mode,
                        "rag_used": chat_request.use_rag,
                        "streaming": True,
                        "source_language": chat_request.language
                    }
                )
                
                saved_assistant_msg = await chat_service.add_message(assistant_message, current_user)
                
                if saved_assistant_msg:
                    print(f"✅ [BG] Message saved (id={saved_assistant_msg.id}). Queuing translation...")
                    translation_service = TranslationService(ai_service.db)
                    await translation_service.queue_message_translation(
                        message_id=saved_assistant_msg.id,
                        content=response_text,
                        source_language=chat_request.language
                    )
            except Exception as bg_err:
                print(f"❌ [BG] Error in post-stream processing: {bg_err}")

        # Generate streaming response
        async def generate_stream():
            full_response = ""
            is_complete = False
            chunk_count = 0
            
            try:
                print(f"🎬 Starting stream for conv {chat_request.conversation_id}")
                async for chunk in ai_service.generate_streaming_response(
                    message=chat_request.message,
                    conversation_id=chat_request.conversation_id,
                    user=current_user,
                    mode=chat_request.mode,
                    use_rag=chat_request.use_rag,
                    additional_context=image_context_str,
                    language_override=chat_request.language
                ):
                    full_response += chunk
                    chunk_count += 1
                    
                    # Periodic logging to show activity in logs (every 50 chunks)
                    if chunk_count % 50 == 0:
                        print(f"  ⚡ Produced {chunk_count} chunks for {chat_request.conversation_id}...")

                    encoded_chunk = json.dumps({"text": chunk})
                    yield f"data: {encoded_chunk}\n\n"
                    
                    await asyncio.sleep(0) # Yield for other tasks
                
                print(f"🏁 Stream production complete. Total chunks: {chunk_count}")
                is_complete = True
                yield "data: [DONE]\n\n"
                
                # Hand off saving tasks to background
                background_tasks.add_task(post_stream_processing, full_response, is_complete)
                
            except asyncio.CancelledError:
                print(f"🚫 Stream cancelled by user for conversation {chat_request.conversation_id}")
                return
            
            except Exception as e:
                print(f"❌ CRITICAL error in streaming response: {e}")
                import traceback
                traceback.print_exc()
                error_chunk = json.dumps({"text": f"\n\n[System Error: {str(e)}]"})
                yield f"data: {error_chunk}\n\n"
                return
            finally:
                print(f"👋 Stream for {chat_request.conversation_id} finished production.")
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "X-Accel-Buffering": "no"  # Disable Nginx buffering
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate streaming response: {str(e)}"
        )


@router.get("/models/info", response_model=Dict[str, Any])
async def get_model_info(
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get AI model information and availability
    """
    try:
        info = await ai_service.get_model_info()
        return info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.get("/models/modes", response_model=Dict[str, str])
async def get_available_modes(
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Get available AI response modes
    """
    try:
        modes = ai_service.get_available_modes()
        return modes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available modes: {str(e)}"
        )


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    conversation_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    rag_service: EnhancedRAGService = Depends(get_rag_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Upload and process a single document for RAG
    
    - **conversation_id**: Conversation to associate the document with
    - **file**: Document file (PDF, DOCX, TXT, PPTX, XLSX, CSV, SDF, images)
    """
    try:
        # Validate conversation belongs to user
        conversation = await chat_service.get_conversation(conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File '{file.filename}' is too large ({len(file_content)} bytes). Maximum size is 10MB."
            )
        
        if len(file_content) == 0:
            supported_formats = rag_service.document_loader.get_supported_formats()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Empty file uploaded",
                    "message": f"The uploaded file '{file.filename}' is empty (0 bytes). Please upload a valid file.",
                    "supported_formats": supported_formats
                }
            )
        
        # Check if file format is supported
        if not rag_service.document_loader.is_supported_format(file.filename or "unknown"):
            from pathlib import Path
            file_extension = Path(file.filename or "unknown").suffix.lower()
            supported_formats = rag_service.document_loader.get_supported_formats()
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Unsupported file format",
                    "message": f"File format '{file_extension}' is not supported. File '{file.filename}' cannot be processed.",
                    "file_extension": file_extension,
                    "filename": file.filename,
                    "supported_formats": supported_formats
                }
            )
        
        # Process document
        result = await rag_service.process_uploaded_file(
            file_content=file_content,
            filename=file.filename or "unknown",
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Upload error: {error_trace}")
        
        supported_formats = rag_service.document_loader.get_supported_formats()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Document processing failed",
                "message": f"Failed to process document '{file.filename}': {str(e)}",
                "supported_formats": supported_formats,
                "filename": file.filename
            }
        )


@router.post("/documents/upload-multiple")
async def upload_multiple_documents(
    conversation_id: UUID,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    rag_service: EnhancedRAGService = Depends(get_rag_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Upload and process multiple documents for RAG
    
    - **conversation_id**: Conversation to associate the documents with
    - **files**: List of document files (PDF, DOCX, TXT, PPTX, XLSX, CSV, SDF, images)
    
    Returns summary of all uploads with individual results
    """
    try:
        # Validate conversation belongs to user
        conversation = await chat_service.get_conversation(conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files provided"
            )
        
        # Process each file
        results = []
        successful_count = 0
        failed_count = 0
        total_chunks = 0
        max_size = 10 * 1024 * 1024  # 10MB per file
        
        for file in files:
            try:
                # Read file content
                file_content = await file.read()
                
                # Validate file size
                if len(file_content) > max_size:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "message": f"File too large ({len(file_content)} bytes). Maximum size is 10MB.",
                        "chunk_count": 0
                    })
                    failed_count += 1
                    continue
                
                if len(file_content) == 0:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "message": "File is empty (0 bytes)",
                        "chunk_count": 0
                    })
                    failed_count += 1
                    continue
                
                # Check if format is supported
                if not rag_service.document_loader.is_supported_format(file.filename or "unknown"):
                    from pathlib import Path
                    file_extension = Path(file.filename or "unknown").suffix.lower()
                    supported_formats = rag_service.document_loader.get_supported_formats()
                    
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "message": f"Unsupported file format '{file_extension}'. Supported: {', '.join(supported_formats)}",
                        "chunk_count": 0
                    })
                    failed_count += 1
                    continue
                
                # Process document
                result = await rag_service.process_uploaded_file(
                    file_content=file_content,
                    filename=file.filename or "unknown",
                    conversation_id=conversation_id,
                    user_id=current_user.id
                )
                
                results.append({
                    "filename": file.filename,
                    "success": result.success,
                    "message": result.message,
                    "chunk_count": result.chunk_count,
                    "processing_time": result.processing_time,
                    "warnings": result.warnings,
                    "file_info": result.file_info
                })
                
                if result.success:
                    successful_count += 1
                    total_chunks += result.chunk_count
                else:
                    failed_count += 1
                    
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "message": f"Error processing file: {str(e)}",
                    "chunk_count": 0
                })
                failed_count += 1
        
        # Return summary
        return {
            "success": successful_count > 0,
            "message": f"Processed {len(files)} files: {successful_count} successful, {failed_count} failed",
            "total_files": len(files),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "total_chunks": total_chunks,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Multiple upload error: {error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Batch upload failed",
                "message": f"Failed to process multiple documents: {str(e)}"
            }
        )


@router.post("/documents/search", response_model=DocumentSearchResponse)
async def search_documents(
    search_request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user),
    rag_service: EnhancedRAGService = Depends(get_rag_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Search documents using semantic similarity
    
    - **query**: Search query
    - **conversation_id**: Conversation to search within
    - **max_results**: Maximum number of results (default: 10)
    - **similarity_threshold**: Minimum similarity score (default: 0.7)
    """
    try:
        # Validate conversation belongs to user
        conversation = await chat_service.get_conversation(
            search_request.conversation_id, current_user
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Search documents
        chunks = await rag_service.search_similar_chunks(
            query=search_request.query,
            conversation_id=search_request.conversation_id,
            user_id=current_user.id,
            max_results=search_request.max_results,
            similarity_threshold=search_request.similarity_threshold
        )
        
        return DocumentSearchResponse(
            chunks=chunks,
            total_results=len(chunks),
            query=search_request.query
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search documents: {str(e)}"
        )


@router.get("/documents/{conversation_id}", response_model=List[Dict[str, Any]])
async def get_conversation_documents(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    rag_service: EnhancedRAGService = Depends(get_rag_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get all document chunks for a conversation
    
    - **conversation_id**: Conversation ID
    """
    try:
        # Validate conversation belongs to user
        conversation = await chat_service.get_conversation(conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get all chunks
        chunks = await rag_service.get_all_conversation_chunks(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        # Group by document
        documents = {}
        for chunk in chunks:
            filename = chunk.metadata.get("filename", "Unknown")
            if filename not in documents:
                documents[filename] = {
                    "filename": filename,
                    "chunk_count": 0,
                    "total_characters": 0,
                    "created_at": chunk.created_at,
                    "embedding_version": chunk.metadata.get("embedding_version", "unknown")
                }
            
            documents[filename]["chunk_count"] += 1
            documents[filename]["total_characters"] += len(chunk.content)
        
        return list(documents.values())
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation documents: {str(e)}"
        )


@router.delete("/documents/{conversation_id}")
async def delete_conversation_documents(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    rag_service: EnhancedRAGService = Depends(get_rag_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Delete all documents for a conversation
    
    - **conversation_id**: Conversation ID
    """
    try:
        # Validate conversation belongs to user
        conversation = await chat_service.get_conversation(conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Delete documents
        success = await rag_service.delete_conversation_documents(
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if success:
            return {"message": "Documents deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete documents"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete documents: {str(e)}"
        )



# ============================================================================
# DEEP RESEARCH ENDPOINTS
# ============================================================================

class DeepResearchRequest(BaseModel):
    """Deep research request model"""
    question: str
    conversation_id: UUID


class DeepResearchResponse(BaseModel):
    """Deep research response model"""
    status: str
    report: str
    citations: List[Dict[str, Any]]
    plan_overview: str
    steps_completed: int
    findings_count: int


@router.post("/deep-research", response_model=DeepResearchResponse)
async def deep_research(
    request: DeepResearchRequest,
    current_user: User = Depends(get_current_user),
    research_service: DeepResearchService = Depends(get_deep_research_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Execute deep research on a biomedical question
    
    This endpoint performs an autonomous multi-step research workflow:
    1. **Planning**: Breaks down the query into sub-topics using PICO/MoA framework
    2. **Researching**: Searches PubMed and web for relevant literature
    3. **Reviewing**: Filters and classifies findings by study type
    4. **Writing**: Synthesizes a comprehensive research report with citations
    
    - **question**: The biomedical research question
    - **conversation_id**: Conversation to associate the research with
    """
    try:
        logger.info(f"🔬 Deep Research initiated by user {current_user.id}")
        logger.info(f"📝 Question: {request.question[:100]}...")
        
        # Security validation
        try:
            security_guard.validate_transaction(request.question)
        except SecurityViolationException as e:
            logger.warning(f"🚨 Security violation in deep research: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.to_dict()
            )
        
        # Validate conversation
        conversation = await chat_service.get_conversation(
            request.conversation_id, current_user
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Add user message
        user_message = MessageCreate(
            conversation_id=request.conversation_id,
            role="user",
            content=f"[Deep Research] {request.question}",
            metadata={"mode": "deep_research"}
        )
        await chat_service.add_message(user_message, current_user)
        
        # 1. Check for Prompt Injection (Pre-Filter)
        injection_check = ai_service.check_for_injection(request.question)
        if injection_check["is_injection"]:
            print(f"🚨 Prompt Injection Detected: {request.question[:50]}...")
            # Save the refusal as a message
            conversation = await chat_service.get_conversation(request.conversation_id, current_user.id)
            if not conversation:
                # This path should ideally not be taken if conversation validation passed above
                conversation = await chat_service.create_conversation(current_user.id, "New Conversation")
            
            await chat_service.add_message(conversation.id, request.question, "user")
            await chat_service.add_message(conversation.id, injection_check["refusal_message"], "assistant")
            
            # Adapting ChatResponse to DeepResearchResponse
            return DeepResearchResponse(
                status="failed",
                report=injection_check["refusal_message"],
                citations=[],
                plan_overview="Injection detected, research aborted.",
                steps_completed=0,
                findings_count=0
            )

        # 2. Check for Deep Research Mode (This line seems misplaced from the original snippet,
        # as this is already the deep research endpoint. I will remove the `if` condition
        # and fix the malformed `_service.run_research` part to just `research_service.run_research`.)
        # The original snippet had `if chat_request.mode == "research":_service.run_research(...)`
        # which is syntactically incorrect and semantically redundant here.
        # I will assume the intent was to proceed with research if not an injection.
        state = await research_service.run_research(
            question=request.question,
            user_id=current_user.id
        )
        
        # Add research report as assistant message
        if state.final_report:
            assistant_message = MessageCreate(
                conversation_id=request.conversation_id,
                role="assistant",
                content=state.final_report,
                metadata={
                    "mode": "deep_research",
                    "citations_count": len(state.citations),
                    "steps_completed": len([s for s in state.steps if s.status == "completed"])
                }
            )
            await chat_service.add_message(assistant_message, current_user)
        
        logger.info(f"✅ Deep Research completed: {len(state.citations)} citations, {len(state.final_report)} chars")
        
        return DeepResearchResponse(
            status=state.status,
            report=state.final_report,
            citations=[
                {"id": c.id, "title": c.title, "url": c.url, "source": c.source}
                for c in state.citations
            ],
            plan_overview=state.plan_overview,
            steps_completed=len([s for s in state.steps if s.status == "completed"]),
            findings_count=len(state.findings)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Deep Research error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deep research failed: {str(e)}"
        )


@router.post("/deep-research/stream")
async def deep_research_stream(
    request: DeepResearchRequest,
    current_user: User = Depends(get_current_user),
    research_service: DeepResearchService = Depends(get_deep_research_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Execute deep research with streaming progress updates
    
    Returns Server-Sent Events (SSE) stream with progress updates:
    - status: Current workflow stage
    - plan: Research plan with sub-topics
    - findings: Number of sources found
    - citations: Validated citations
    - complete: Final report
    
    - **question**: The biomedical research question
    - **conversation_id**: Conversation to associate the research with
    """
    try:
        # Security validation
        try:
            security_guard.validate_transaction(request.question)
        except SecurityViolationException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.to_dict()
            )
        
        # Validate conversation
        conversation = await chat_service.get_conversation(
            request.conversation_id, current_user
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Add user message
        user_message = MessageCreate(
            conversation_id=request.conversation_id,
            role="user",
            content=f"[Deep Research] {request.question}",
            metadata={"mode": "deep_research"}
        )
        await chat_service.add_message(user_message, current_user)
        
        async def generate_stream():
            final_report = ""
            citations_count = 0
            
            async for update in research_service.run_research_streaming(
                question=request.question,
                user_id=current_user.id
            ):
                yield f"data: {update}\n\n"
                
                # Track final report for saving
                try:
                    import json
                    data = json.loads(update.strip())
                    if data.get("type") == "complete":
                        final_report = data.get("report", "")
                        citations_count = len(data.get("citations", []))
                        logger.info(f"📄 Deep Research report captured: {len(final_report)} chars, {citations_count} citations")
                    elif data.get("type") == "error":
                        # Capture error as the report
                        final_report = f"# Research Error\n\nThe deep research encountered an error: {data.get('message', 'Unknown error')}\n\nPlease try again or rephrase your query."
                        logger.warning(f"⚠️ Deep Research error captured: {data.get('message')}")
                except Exception as parse_error:
                    logger.debug(f"Could not parse update: {parse_error}")
                    pass
            
            # ALWAYS save a message to conversation - use fallback if empty
            if not final_report:
                final_report = f"# Research Report: {request.question}\n\n**Note:** The research process completed but did not produce a detailed report. This may be due to:\n- Limited available literature on this specific topic\n- API rate limiting\n- Network issues\n\nPlease try again in a few moments or try a different query."
                logger.warning(f"⚠️ Deep Research produced empty report, using fallback")
            
            assistant_message = MessageCreate(
                conversation_id=request.conversation_id,
                role="assistant",
                content=final_report,
                metadata={
                    "mode": "deep_research",
                    "citations_count": citations_count,
                    "streaming": True
                }
            )
            await chat_service.add_message(assistant_message, current_user)
            logger.info(f"✅ Deep Research message saved to conversation {request.conversation_id}")
            
            yield "data: [DONE]\n\n"

        
        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Deep Research streaming error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deep research streaming failed: {str(e)}"
        )
