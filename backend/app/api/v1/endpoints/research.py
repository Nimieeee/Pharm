from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from app.core.security import get_current_user
from app.models.user import User
from app.services.research_service import ResearchService

router = APIRouter()
logger = logging.getLogger(__name__)

class DeepResearchRequest(BaseModel):
    question: str
    conversation_id: str
    metadata: Optional[Dict[str, Any]] = None

def get_research_service() -> ResearchService:
    return ResearchService()

@router.post("/stream")
async def stream_deep_research(
    request: DeepResearchRequest,
    current_user: User = Depends(get_current_user),
    service: ResearchService = Depends(get_research_service)
):
    """
    Stream deep research progress and results using SSE.
    """
    logger.info(f"🧠 Deep Research requested by {current_user.id}: {request.question}")
    
    return StreamingResponse(
        service.stream_deep_research(request.question, request.conversation_id),
        media_type="text/event-stream"
    )
