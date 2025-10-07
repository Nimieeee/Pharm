"""
AI Chat API endpoints
"""

from typing import Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import Client

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.ai import AIService
from app.services.chat import ChatService
from app.models.user import User
from app.models.conversation import MessageCreate

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request model"""
    message: str
    conversation_id: UUID
    mode: str = "detailed"  # "fast" or "detailed"
    use_rag: bool = True


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
            content=chat_request.message
        )
        
        await chat_service.add_message(user_message, current_user)
        
        # Generate AI response
        ai_response = await ai_service.generate_response(
            message=chat_request.message,
            conversation_id=chat_request.conversation_id,
            user=current_user,
            mode=chat_request.mode,
            use_rag=chat_request.use_rag
        )
        
        # Add AI response to conversation
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
        
        return ChatResponse(
            response=ai_response,
            conversation_id=chat_request.conversation_id,
            mode=chat_request.mode,
            context_used=chat_request.use_rag
        )
        
    except HTTPException:
        raise
    except Exception as e:
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
            content=chat_request.message
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