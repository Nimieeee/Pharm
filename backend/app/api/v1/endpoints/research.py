from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.research_service import ResearchService
from app.services.enhanced_rag import EnhancedRAGService
from supabase import Client

router = APIRouter()
logger = logging.getLogger(__name__)

class DeepResearchRequest(BaseModel):
    question: str
    conversation_id: str
    metadata: Optional[Dict[str, Any]] = None

def get_research_service() -> ResearchService:
    return ResearchService()

def get_rag_service(db: Client = Depends(get_db)) -> EnhancedRAGService:
    return EnhancedRAGService(db)

@router.post("/stream")
async def stream_deep_research(
    request: DeepResearchRequest,
    current_user: User = Depends(get_current_user),
    service: ResearchService = Depends(get_research_service),
    rag_service: EnhancedRAGService = Depends(get_rag_service)
):
    """
    Stream deep research progress and results using SSE.
    Now includes document context from uploaded files.
    """
    logger.info(f"🧠 Deep Research requested by {current_user.id}: {request.question}")
    
    # Fetch document context from RAG if available
    document_context = ""
    try:
        context = await rag_service.get_conversation_context(
            query=request.question,
            conversation_id=UUID(request.conversation_id),
            user_id=current_user.id,
            max_chunks=10
        )
        if context and context.strip():
            document_context = f"""\n\n[IMPORTANT: The user has uploaded documents. Use this context in your research:]\n\n{context}\n\n[End of uploaded document context. Now proceed with web research to supplement this information.]\n\n"""
            logger.info(f"📄 Added {len(context)} chars of document context to research")
    except Exception as e:
        logger.warning(f"⚠️ Failed to fetch document context: {e}")
    
    # Combine question with document context
    enhanced_question = f"{request.question}{document_context}"
    
    return StreamingResponse(
        service.stream_deep_research(enhanced_question, request.conversation_id),
        media_type="text/event-stream"
    )
