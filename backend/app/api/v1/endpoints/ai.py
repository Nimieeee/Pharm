"""
AI Chat API endpoints

FULLY DECOUPLED: Uses ServiceContainer for all service access.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from supabase import Client

from app.core.database import get_db
from app.core.container import container as service_container, get_container, ServiceContainer
from app.core.security import get_current_user
from app.services.ai import AIService
from app.services.chat import ChatService
from app.services.deep_research import DeepResearchService
from app.services.enhanced_rag import EnhancedRAGService
from app.services.image_gen import ImageGenerationService
from app.models.user import User
from app.models.conversation import MessageCreate
from app.models.document import DocumentUploadResponse, DocumentSearchRequest, DocumentSearchResponse
from app.security import LLMSecurityGuard, SecurityViolationException, get_hardened_prompt
import logging
import json
import asyncio
import base64

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
    parent_id: Optional[UUID] = None  # For DAG branching: ID of the preceding message
    user_message_id: Optional[UUID] = None  # For branching: regenerate response to an existing user message


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    conversation_id: UUID
    mode: str
    context_used: bool


def get_ai_service(db: Client = Depends(get_db)) -> AIService:
    """Get AI service from container"""
    # Container should be initialized at app startup
    if not service_container.is_initialized():
        service_container.initialize(db)
    return service_container.get('ai_service')


def get_chat_service(db: Client = Depends(get_db)):
    """Get chat service from container"""
    if not service_container.is_initialized():
        service_container.initialize(db)
    return service_container.get('chat_service')


def get_rag_service(db: Client = Depends(get_db)):
    """Get RAG service from container"""
    if not service_container.is_initialized():
        service_container.initialize(db)
    return service_container.get('rag_service')


def get_deep_research_service(db: Client = Depends(get_db)):
    """Get deep research service from container"""
    if not service_container.is_initialized():
        service_container.initialize(db)
    return service_container.get('deep_research_service')


def get_image_gen_service(db: Client = Depends(get_db)):
    """Get image generation service from container"""
    if not service_container.is_initialized():
        service_container.initialize(db)
    return service_container.get('image_gen_service')


def get_translation_service(db: Client = Depends(get_db)):
    """Get translation service from container"""
    if not service_container.is_initialized():
        service_container.initialize(db)
    return service_container.get('translation_service')


class ImageGenerationRequest(BaseModel):
    """Image generation request model"""
    prompt: str
    conversation_id: UUID


@router.post("/image-generation")
async def generate_image(
    request: ImageGenerationRequest,
    current_user: User = Depends(get_current_user),
    image_service: ImageGenerationService = Depends(get_image_gen_service),
    chat_service: ChatService = Depends(get_chat_service),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Generate an image based on a prompt
    """
    print(f"🎨 Image Generation requested by user {current_user.id}")
    print(f"📝 Original Prompt: {request.prompt}")
    
    try:
        # Step 1: Enhance the prompt using Mistral (Prompt Engineering)
        print("✨ Enhancing prompt with Mistral...")
        # Instructions for the AI model enhancing the prompt:
        # 6. Output ONLY the enhanced prompt. No introductions or quotes.
        # 7. CRITICAL: If the user asks for a diagram/labels, explicitly instruct the generator to use "legible, correct text" or "no text labels" if accuracy cannot be guaranteed. AVOID GIBBERISH TEXT.
        # 8. If the user asks for a specific condition (e.g. "pathology"), ensure the prompt emphasizes ACCURATE MEDICAL VISUALIZATION.
        enhanced_prompt = await ai_service.enhance_image_prompt(request.prompt)
        print(f"✨ Enhanced Prompt: {enhanced_prompt}")
        
        logger.info(f"Generating image for user {current_user.id}")
        logger.info(f"Original: {request.prompt}")
        logger.info(f"Enhanced: {enhanced_prompt}")
        
        # Call the image generation service with the ENHANCED prompt
        result = await image_service.generate_image(enhanced_prompt)
        
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
        # 2. Save assistant response (image URL)
        if result.get("status") == "success":
            img_url = result.get("image_url")
            assistant_message = f"![{request.prompt}]({img_url})"
        else:
            assistant_message = f"Failed to generate image: {result.get('error', 'Unknown error')}"
             
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
            "image_url": img_url,
            "markdown": assistant_message
        }
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image generation failed: {str(e)}"
        )



def get_chat_orchestrator(
    db: Client = Depends(get_db)
):
    from app.services.chat_orchestrator import ChatOrchestratorService
    return ChatOrchestratorService(db)

@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    orchestrator = Depends(get_chat_orchestrator)
):
    """Generate AI response for a chat message"""
    try:
        if chat_request.message.strip().lower().startswith("/image"):
            return ChatResponse(response="", conversation_id=chat_request.conversation_id, mode=chat_request.mode, context_used=False)
            
        result = await orchestrator.process_chat_request(chat_request, current_user)
        return ChatResponse(
            response=result["response"],
            conversation_id=chat_request.conversation_id,
            mode=chat_request.mode,
            context_used=result["context_used"]
        )
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat/stream")
async def chat_stream(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    orchestrator = Depends(get_chat_orchestrator),
    chat_service: ChatService = Depends(get_chat_service),
    ai_service: AIService = Depends(get_ai_service)
):
    """Generate streaming AI response for a chat message"""
    try:
        conversation = await chat_service.get_conversation(chat_request.conversation_id, current_user)
        if not conversation: raise HTTPException(status_code=404, detail="Conversation not found")

        original_message = chat_request.message.strip()
        if original_message.lower().startswith("lab:"):
            from app.core.container import container
            from app.services.lab_report import LabReportService
            from app.services.enhanced_rag import EnhancedRAGService

            chat_request.message = original_message[4:].strip()
            # Save user message
            user_message = MessageCreate(conversation_id=chat_request.conversation_id, role="user", content=original_message, metadata=chat_request.metadata)
            saved_msg = await chat_service.add_message(user_message, current_user)

            async def lab_report_stream():
                try:
                    # Send initial metadata chunk with the USER ID
                    if saved_msg:
                        meta_data = {
                            "type": "meta",
                            "user_message_id": str(saved_msg.id),
                            "is_branching": True
                        }
                        yield f"data: {json.dumps(meta_data)}\n\n"

                    # Use container for services
                    lab_service = container.get('lab_report_service')
                    rag_service = container.get('rag_service')
                    yield "data: " + json.dumps({"text": "📝 **Generating Lab Report...**\n\n"}) + "\n\n"
                    context = await rag_service.get_conversation_context(chat_request.message, chat_request.conversation_id, current_user.id, 20)
                    if context: yield "data: " + json.dumps({"text": "📄 Found context...\n"}) + "\n\n"
                    yield "data: " + json.dumps({"text": "🔬 Analyzing data...\n\n"}) + "\n\n"

                    full_context = (context or "")
                    result = await lab_service.generate_report(chat_request.message, full_context, "Standard", None)
                    if result.get("error"): yield "data: " + json.dumps({"text": f"❌ Error: {result.get('error')}"}) + "\n\n"
                    else: yield "data: " + json.dumps({"text": result.get("full_report", "")}) + "\n\n"

                    # Create the branch in assistant_responses instead of messages
                    if saved_msg:
                        await chat_service.create_response_branch(
                            user_message_id=saved_msg.id,
                            content=result.get("full_report", ""),
                            model_used="lab_report",
                            token_count=len(result.get("full_report", "")) // 4,
                            metadata={"mode": "lab_report"}
                        )
                except Exception as e:
                    logger.error(f"Lab report stream error: {e}")
                    yield "data: " + json.dumps({"text": f"❌ Error: {str(e)}"}) + "\n\n"
                yield "data: [DONE]\n\n"

            # Add CORS headers to StreamingResponse
            return StreamingResponse(
                lab_report_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Authorization",
                    "Access-Control-Allow-Credentials": "true"
                }
            )

        if original_message.lower().startswith("/image"):
             async def empty_stream(): yield "data: [DONE]\n\n"
             return StreamingResponse(empty_stream(), media_type="text/event-stream")

        # Add CORS headers to main streaming response
        return StreamingResponse(
            orchestrator.stream_chat_request(chat_request, current_user, background_tasks),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Credentials": "true"
            }
        )
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/conversations/{conversation_id}/messages/{message_id}/thread")
async def get_thread_from_message(
    conversation_id: UUID,
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Return the full message thread (root → leaf) walking from the given message upward.
    Then include all child messages from that message downward on the active branch.
    Used by branch navigation to switch to a different branch.
    """
    try:
        thread = await chat_service.get_message_thread(message_id, current_user, include_children=True)
        return [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "parent_id": str(m.parent_id) if m.parent_id else None,
                "created_at": m.created_at,
                "translations": m.metadata.get("translations") if m.metadata else None,
                "metadata": m.metadata,
            }
            for m in thread
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        
        # Create image analyzer function (injected to avoid circular dependency)
        async def image_analyzer(image_bytes: bytes) -> str:
            """Local image analyzer to avoid circular import with AIService"""
            try:
                from app.services.ai import AIService
                ai_service_temp = AIService(chat_service.db)
                b64_str = base64.b64encode(image_bytes).decode('utf-8')
                data_url = f"data:image/jpeg;base64,{b64_str}"
                return await ai_service_temp.analyze_image(data_url)
            except Exception as e:
                logger.error(f"Image analysis failed: {e}")
                return ""

        # Process document WITH image analyzer injected
        result = await rag_service.process_uploaded_file(
            file_content=file_content,
            filename=file.filename or "unknown",
            conversation_id=conversation_id,
            user_id=current_user.id,
            image_analyzer=image_analyzer  # Injected dependency
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


@router.get("/image-proxy")
async def proxy_image(
    prompt: str,
    model: str = "flux",
    width: int = 512,
    height: int = 512,
    seed: int = 42,
):
    """
    Proxy endpoint to fetch images from Pollinations (hiding API key).
    Publicly accessible to allow embedding in Markdown.
    """
    try:
        service = ImageGenerationService()
        image_bytes = await service.fetch_image_from_pollinations(prompt, model, width, height, seed)
        
        # --- WATERMARK LOGIC ---
        try:
            from PIL import Image
            import io
            import os
            
            # Paths
            # Assuming backend is running in /backend, so frontend is ../frontend
            # But the CWD might be different. I'll rely on absolute paths or relative to project root found via file inspection
            # CWD is usually project root or backend dir. Let's try relative to this file first or absolute.
            # Best to use the known path structure: /Users/mac/Desktop/phhh/frontend/public/Benchside.png
            logo_path = "/Users/mac/Desktop/phhh/frontend/public/Benchside.png"
            
            if os.path.exists(logo_path):
                # Load main image
                main_image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
                
                # Load logo
                logo = Image.open(logo_path).convert("RGBA")
                
                # Resize logo (e.g., 20% of main image width)
                target_width = int(main_image.width * 0.20)
                aspect_ratio = logo.height / logo.width
                target_height = int(target_width * aspect_ratio)
                
                logo = logo.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Position: Bottom-Right with padding
                padding = 20
                position = (
                    main_image.width - logo.width - padding,
                    main_image.height - logo.height - padding
                )
                
                # Overlay
                # Create a transparent layer for the logo
                watermark_layer = Image.new("RGBA", main_image.size, (0,0,0,0))
                watermark_layer.paste(logo, position, logo)
                
                # Composite
                final_image = Image.alpha_composite(main_image, watermark_layer)
                
                # Convert back to JPEG
                output_buffer = io.BytesIO()
                final_image.convert("RGB").save(output_buffer, format="JPEG", quality=95)
                image_bytes = output_buffer.getvalue()
            else:
                print(f"⚠️ Watermark logo not found at {logo_path}")
                
        except Exception as wm_error:
            print(f"⚠️ Failed to apply watermark: {wm_error}")
            # Fallback to original image if watermark fails
            pass
            
        return Response(content=image_bytes, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






# ============================================================================
# DEEP RESEARCH ENDPOINTS
# ============================================================================

class DeepResearchRequest(BaseModel):
    """Deep research request model"""
    question: str
    conversation_id: UUID
    metadata: Optional[Dict[str, Any]] = None



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
    chat_service: ChatService = Depends(get_chat_service),
    ai_service: AIService = Depends(get_ai_service),
    rag_service: EnhancedRAGService = Depends(get_rag_service)
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
            content=request.question,
            metadata={"mode": "deep_research"}
        )
        await chat_service.add_message(user_message, current_user)
        
        # 1. Fetch document context from RAG if available
        document_context = ""
        try:
            context = await rag_service.get_conversation_context(
                query=request.question,
                conversation_id=request.conversation_id,
                user_id=current_user.id,
                max_chunks=10
            )
            if context and context.strip():
                document_context = f"""\n\n[IMPORTANT: The user has uploaded documents. Use this context in your research:]\n\n{context}\n\n[End of uploaded document context. Now proceed with web research to supplement this information.]\n\n"""
                logger.info(f"📄 Added {len(context)} chars of document context to research")
        except Exception as rag_err:
            logger.warning(f"⚠️ Failed to fetch document context: {rag_err}")
            
        enhanced_question = f"{request.question}{document_context}"

        # 2. Check for Prompt Injection (Pre-Filter)
        injection_check = ai_service.check_for_injection(request.question)
        if injection_check["is_injection"]:
            logger.warning(f"🚨 Prompt Injection Detected: {request.question[:50]}...")
            
            # Save the refusal as a message
            user_message = MessageCreate(
                conversation_id=request.conversation_id,
                role="user",
                content=request.question,
                metadata={"mode": "deep_research", **(request.metadata or {})}
            )
            await chat_service.add_message(user_message, current_user)
            
            refusal_message = MessageCreate(
                conversation_id=request.conversation_id,
                role="assistant",
                content=injection_check["refusal_message"],
                metadata={"mode": "deep_research", "security_refusal": True}
            )
            await chat_service.add_message(refusal_message, current_user)
            
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
            question=enhanced_question,
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
    chat_service: ChatService = Depends(get_chat_service),
    rag_service: EnhancedRAGService = Depends(get_rag_service)
):
    """
    Execute deep research with streaming progress updates.
    Now includes document context and database persistence (meta events).
    """
    try:
        logger.info(f"🔬 Deep Research stream initiated by {current_user.id}: {request.question[:100]}...")
        
        # 1. Security validation
        try:
            security_guard.validate_transaction(request.question)
        except SecurityViolationException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=e.to_dict()
            )
        
        # 2. Fetch document context from RAG if available
        document_context = ""
        try:
            context = await rag_service.get_conversation_context(
                query=request.question,
                conversation_id=request.conversation_id,
                user_id=current_user.id,
                max_chunks=10
            )
            if context and context.strip():
                document_context = f"""\n\n[IMPORTANT: The user has uploaded documents. Use this context in your research:]\n\n{context}\n\n[End of uploaded document context. Now proceed with web research to supplement this information.]\n\n"""
                logger.info(f"📄 Added {len(context)} chars of document context to research")
        except Exception as rag_err:
            logger.warning(f"⚠️ Failed to fetch document context: {rag_err}")
        
        # Combined question with document context for the researcher
        enhanced_question = f"{request.question}{document_context}"
        
        # 3. Database Persistence - Save User Message
        try:
            user_message = MessageCreate(
                conversation_id=request.conversation_id,
                role="user",
                content=request.question,
                metadata={"mode": "deep_research", **(request.metadata or {})}
            )
            saved_user_msg = await chat_service.add_message(user_message, current_user)
            
            # We no longer pre-create an assistant message in the `messages` table.
            # The report will be stored in `assistant_responses` branch at the end.
            saved_assistant_msg_id = None
        except Exception as db_err:
            logger.error(f"❌ Failed to persist research messages: {db_err}")
            saved_user_msg = None
            saved_assistant_msg_id = None
        
        async def generate_stream():
            # Yield metadata first
            if saved_user_msg:
                import uuid
                # Generate a temporary UUID for the frontend to bind events
                saved_assistant_msg_id = str(uuid.uuid4())
                meta_data = {
                    "type": "meta",
                    "user_message_id": str(saved_user_msg.id),
                    "assistant_message_id": saved_assistant_msg_id,
                    "is_branching": True
                }
                yield f"data: {json.dumps(meta_data)}\n\n"
            
            # Use non-destructive heartbeat: race generator against a sleep timer
            # CRITICAL: asyncio.wait_for CANCELS the awaitable on timeout, which
            # destroys the async generator's state. Instead, use asyncio.wait with
            # FIRST_COMPLETED so the __anext__ task stays alive across heartbeats.
            research_gen = research_service.run_research_streaming(
                question=enhanced_question,
                user_id=current_user.id
            )
            aiter = research_gen.__aiter__()
            next_task = asyncio.ensure_future(aiter.__anext__())
            
            while True:
                # Race the generator against a 10s sleep
                sleep_task = asyncio.ensure_future(asyncio.sleep(10.0))
                done, pending = await asyncio.wait(
                    {next_task, sleep_task},
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                if next_task in done:
                    # Generator yielded a value
                    sleep_task.cancel()
                    try:
                        update = next_task.result()
                    except StopAsyncIteration:
                        break
                    
                    yield f"data: {update}\n\n"
                    
                    # Track final report for saving
                    try:
                        data = json.loads(update.strip())
                        if data.get("type") == "complete":
                            final_report = data.get("report", "")
                            citations_count = len(data.get("citations", []))
                            logger.info(f"📄 Deep Research report captured: {len(final_report)} chars, {citations_count} citations")
                        elif data.get("type") == "error":
                            final_report = f"# Research Error\n\nThe deep research encountered an error: {data.get('message', 'Unknown error')}\n\nPlease try again or rephrase your query."
                            logger.warning(f"⚠️ Deep Research error captured: {data.get('message')}")
                    except Exception:
                        pass
                    
                    # Request next value from generator
                    next_task = asyncio.ensure_future(aiter.__anext__())
                else:
                    # Sleep completed first — generator is still working
                    # Send heartbeat to keep SSE connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
            
            # ALWAYS save a message to conversation - use fallback if empty
            if not final_report:
                final_report = f"# Research Report: {request.question}\n\n**Note:** The research process completed but did not produce a detailed report. This may be due to API rate limits or network issues."
                logger.warning(f"⚠️ Deep Research produced empty report, using fallback")
            
            # Update or create the assistant message as a branch
            if saved_user_msg:
                try:
                    await chat_service.create_response_branch(
                        user_message_id=saved_user_msg.id,
                        content=final_report,
                        model_used="deep_research",
                        token_count=len(final_report) // 4,
                        metadata={
                            "mode": "deep_research",
                            "citations_count": citations_count,
                            "streaming": False,
                            "citations": data.get("citations", []) if 'data' in locals() else []
                        }
                    )
                    logger.info(f"✅ Deep Research history saved as branch for: {saved_user_msg.id}")
                except Exception as meta_e:
                    logger.error(f"❌ Failed to persist final research report branch: {meta_e}")
            
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

