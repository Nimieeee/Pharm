"""
AI Chat API endpoints
"""

from typing import Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import Client

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.ai import AIService
from app.services.chat import ChatService
from app.services.enhanced_rag import EnhancedRAGService
from app.models.user import User
from app.models.conversation import MessageCreate
from app.models.document import DocumentUploadResponse, DocumentSearchRequest, DocumentSearchResponse

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: UUID
    mode: str = "detailed"  # "fast" or "detailed"
    use_rag: bool = True
    metadata: Dict[str, Any] = {}


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
        
        # Generate AI response
        print("🤖 Calling AI service...")
        ai_response = await ai_service.generate_response(
            message=chat_request.message,
            conversation_id=chat_request.conversation_id,
            user=current_user,
            mode=chat_request.mode,
            use_rag=chat_request.use_rag
        )
        print(f"✅ AI response generated: {len(ai_response)} chars")
        
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
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Generate streaming AI response for a chat message
    
    Returns Server-Sent Events (SSE) stream
    """
    try:
        # Validate conversation belongs to user
        conversation = await chat_service.get_conversation(
            chat_request.conversation_id, current_user
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Add user message to conversation
        user_message = MessageCreate(
            conversation_id=chat_request.conversation_id,
            role="user",
            content=chat_request.message,
            metadata=chat_request.metadata
        )
        
        await chat_service.add_message(user_message, current_user)
        
        # Generate streaming response
        async def generate_stream():
            full_response = ""
            
            async for chunk in ai_service.generate_streaming_response(
                message=chat_request.message,
                conversation_id=chat_request.conversation_id,
                user=current_user,
                mode=chat_request.mode,
                use_rag=chat_request.use_rag
            ):
                full_response += chunk
                yield f"data: {chunk}\n\n"
            
            # Add complete response to conversation
            assistant_message = MessageCreate(
                conversation_id=chat_request.conversation_id,
                role="assistant",
                content=full_response,
                metadata={
                    "mode": chat_request.mode,
                    "rag_used": chat_request.use_rag,
                    "streaming": True
                }
            )
            
            await chat_service.add_message(assistant_message, current_user)
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream"
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
    Upload and process a document for RAG
    
    - **conversation_id**: Conversation to associate the document with
    - **file**: Document file (PDF, DOCX, TXT, PPTX, XLSX, CSV, images)
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
                detail="File too large. Maximum size is 10MB"
            )
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
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