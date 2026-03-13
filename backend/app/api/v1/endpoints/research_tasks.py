from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.research_tasks import BackgroundResearchService
from supabase import Client

router = APIRouter()
logger = logging.getLogger(__name__)

def get_background_research_service(db: Client = Depends(get_db)) -> BackgroundResearchService:
    return BackgroundResearchService(db)

@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_research_task(
    question: str,
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BackgroundResearchService = Depends(get_background_research_service)
):
    """
    Submit a research question to be processed in the background.
    """
    try:
        task_id = await service.create_task(
            user_id=current_user.id,
            conversation_id=conversation_id,
            question=question
        )
        return {"task_id": task_id, "status": "PENDING"}
    except Exception as e:
        logger.error(f"❌ Failed to submit research task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit task: {str(e)}"
        )

@router.get("/tasks/my")
async def list_my_tasks(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    service: BackgroundResearchService = Depends(get_background_research_service)
):
    """
    List recent background research tasks for the current user.
    """
    return await service.get_user_tasks(current_user.id, limit)

@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    service: BackgroundResearchService = Depends(get_background_research_service)
):
    """
    Get the current status and result of a specific research task.
    """
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Check ownership
    if str(task["user_id"]) != str(current_user.id) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
        
    return task
