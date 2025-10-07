"""
Chat API endpoints
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from supabase import Client

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.chat import ChatService
from app.services.enhanced_rag import EnhancedRAGService
from app.models.user import User
from app.models.conversation import (
    Conversation, ConversationCreate, ConversationUpdate, ConversationWithMessages,
    Message, MessageCreate
)
from app.models.document import DocumentUploadResponse

router = APIRouter()


def get_chat_service(db: Client = Depends(get_db)) -> ChatService:
    """Get chat service"""
    return ChatService(db)


def get_rag_service(db: Client = Depends(get_db)) -> EnhancedRAGService:
    """Get Enhanced RAG service with LangChain"""
    return EnhancedRAGService(db)


@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get all conversations for the current user
    
    Returns list of conversations ordered by last activity
    """
    try:
        conversations = await chat_service.get_user_conversations(current_user)
        return conversations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Create a new conversation
    
    - **title**: Conversation title
    """
    try:
        conversation = await chat_service.create_conversation(conversation_data, current_user)
        return conversation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get a specific conversation with all messages
    
    Returns conversation details and message history
    """
    try:
        conversation = await chat_service.get_conversation_with_messages(
            conversation_id, current_user
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.put("/conversations/{conversation_id}", response_model=Conversation)
async def update_conversation(
    conversation_id: UUID,
    conversation_data: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Update a conversation
    
    - **title**: New conversation title
    """
    try:
        conversation = await chat_service.update_conversation(
            conversation_id, conversation_data, current_user
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return conversation
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update conversation: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Delete a conversation and all its data
    
    This will permanently delete the conversation, all messages, and uploaded documents
    """
    try:
        success = await chat_service.delete_conversation(conversation_id, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/messages", response_model=Message)
async def add_message(
    conversation_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Add a message to a conversation
    
    - **role**: Message role ('user' or 'assistant')
    - **content**: Message content
    - **metadata**: Optional metadata
    """
    try:
        # Ensure conversation_id matches
        message_data.conversation_id = conversation_id
        
        message = await chat_service.add_message(message_data, current_user)
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add message: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def get_messages(
    conversation_id: UUID,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Get messages for a conversation
    
    - **limit**: Optional limit on number of messages to return
    """
    try:
        messages = await chat_service.get_conversation_messages(
            conversation_id, current_user, limit
        )
        return messages
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.post("/conversations/{conversation_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    conversation_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    rag_service: EnhancedRAGService = Depends(get_rag_service)
):
    """
    Upload a document to a conversation
    
    Supported file types: PDF, TXT, MD, DOCX, PPTX
    """
    try:
        # Check if conversation exists and belongs to user
        conversation = await chat_service.get_conversation(conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Validate file type
        allowed_extensions = {'pdf', 'txt', 'md', 'docx', 'pptx'}
        file_extension = file.filename.lower().split('.')[-1] if file.filename else ''
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )
        
        # Process file
        result = await rag_service.process_uploaded_file(
            file_content, file.filename, conversation_id, current_user.id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}/documents")
async def delete_conversation_documents(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    rag_service: EnhancedRAGService = Depends(get_rag_service)
):
    """
    Delete all documents from a conversation
    """
    try:
        # Check if conversation exists and belongs to user
        conversation = await chat_service.get_conversation(conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Delete documents
        success = await rag_service.delete_conversation_documents(
            conversation_id, current_user.id
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