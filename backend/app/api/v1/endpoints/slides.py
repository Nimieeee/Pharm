from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio, json, io, uuid

from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

# --- Request/Response Models ---

class SlideOutlineRequest(BaseModel):
    topic: str
    num_slides: int = 12
    context: Optional[str] = None
    conversation_id: Optional[str] = None  # To pull RAG context

class SlideOutline(BaseModel):
    title: str
    subtitle: Optional[str] = None
    theme: str = "ocean_gradient"
    slides: List[Dict[str, Any]]

class SlideGenerateRequest(BaseModel):
    outline: SlideOutline
    generate_images: bool = True

# --- Storage for in-progress jobs ---
slide_jobs: dict = {}  # job_id -> {"status": ..., "pptx_bytes": ...}

# --- Endpoints ---

@router.post("/outline")
async def generate_slide_outline(
    request: SlideOutlineRequest,
    current_user: User = Depends(get_current_user)
):
    """Step 1: Generate editable JSON outline from topic"""
    try:
        from app.services.slide_service import get_slide_service
        
        slide_service = get_slide_service()
        
        # Pull conversation context if provided
        context = None
        if request.conversation_id:
            from app.services.enhanced_rag import EnhancedRAGService
            from app.core.database import get_db
            rag = EnhancedRAGService(get_db())
            context = await rag.get_conversation_context(request.conversation_id)
        
        outline = await slide_service.generate_outline(
            topic=request.topic,
            context=context or request.context,
            num_slides=request.num_slides
        )
        
        return outline
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate outline: {str(e)}"
        )

@router.post("/generate")
async def generate_slides(
    request: SlideGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """Step 2-4: Generate PPTX from approved outline. Returns SSE progress."""
    try:
        from app.services.slide_service import get_slide_service
        
        slide_service = get_slide_service()
        job_id = str(uuid.uuid4())
        slide_jobs[job_id] = {"status": "started", "pptx_bytes": None}
        
        async def event_generator():
            async def on_progress(data):
                yield {"event": "progress", "data": json.dumps(data)}
            
            try:
                pptx_bytes = await slide_service.generate_slides(
                    outline=request.outline.dict(),
                    generate_images=request.generate_images,
                    on_progress=on_progress
                )
                slide_jobs[job_id]["pptx_bytes"] = pptx_bytes
                slide_jobs[job_id]["status"] = "complete"
                yield {"event": "complete", "data": json.dumps({"job_id": job_id})}
            except Exception as e:
                slide_jobs[job_id]["status"] = "error"
                yield {"event": "error", "data": json.dumps({"error": str(e)})}
        
        return EventSourceResponse(event_generator())
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate slides: {str(e)}"
        )

@router.get("/download/{job_id}")
async def download_slides(job_id: str, current_user: User = Depends(get_current_user)):
    """Download generated PPTX"""
    job = slide_jobs.get(job_id)
    if not job or not job["pptx_bytes"]:
        raise HTTPException(404, "Slide job not found or not complete")
    
    return StreamingResponse(
        io.BytesIO(job["pptx_bytes"]),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename=benchside_slides_{job_id[:8]}.pptx"}
    )
