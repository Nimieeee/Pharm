from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
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
# Using a dictionary to store progress queues
slide_jobs: dict = {}  # job_id -> {"status": ..., "pptx_bytes": ..., "queue": asyncio.Queue}

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
        import logging
        logging.getLogger("app.slides").error(f"Outline generation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate outline: {str(e)}"
        )

@router.post("/generate")
async def generate_slides(
    request: SlideGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Step 2-4: Start background PPTX generation. Returns job_id."""
    try:
        job_id = str(uuid.uuid4())
        slide_jobs[job_id] = {
            "status": "started", 
            "pptx_bytes": None, 
            "queue": asyncio.Queue(),
            "current": 0,
            "total": len(request.outline.slides),
            "message": "Initializing..."
        }
        
        background_tasks.add_task(run_slide_generation, job_id, request)
        return {"job_id": job_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_slide_generation(job_id: str, request: SlideGenerateRequest):
    from app.services.slide_service import get_slide_service
    slide_service = get_slide_service()
    
    async def on_progress(data):
        # Update internal state for polling
        slide_jobs[job_id].update({
            "current": data.get("current", 0),
            "total": data.get("total", 0),
            "message": data.get("message", "")
        })
        # Push to queue for SSE
        await slide_jobs[job_id]["queue"].put(data)
    
    try:
        pptx_bytes = await slide_service.generate_slides(
            outline=request.outline.dict(),
            generate_images=request.generate_images,
            on_progress=on_progress
        )
        slide_jobs[job_id]["pptx_bytes"] = pptx_bytes
        slide_jobs[job_id]["status"] = "complete"
        await slide_jobs[job_id]["queue"].put({"status": "complete", "job_id": job_id})
    except Exception as e:
        slide_jobs[job_id]["status"] = "error"
        await slide_jobs[job_id]["queue"].put({"status": "error", "error": str(e)})

@router.get("/status/{job_id}")
async def get_slide_status(job_id: str):
    """SSE endpoint for slide generation progress"""
    if job_id not in slide_jobs:
        raise HTTPException(404, "Job not found")

    async def event_generator():
        queue = slide_jobs[job_id]["queue"]
        while True:
            data = await queue.get()
            yield {"event": "message", "data": json.dumps(data)}
            if data.get("status") in ["complete", "error"]:
                break
    
    return EventSourceResponse(event_generator())

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

@router.post("/outline/export/manuscript")
async def export_outline_as_manuscript(
    outline: SlideOutline,
    current_user: User = Depends(get_current_user)
):
    """
    Compatibility route to export a slide outline as a Word manuscript.
    Proxies to ManuscriptFormatter logic.
    """
    try:
        from app.services.manuscript_formatter import ManuscriptFormatter
        from app.services.multi_provider import get_multi_provider
        
        formatter = ManuscriptFormatter(multi_provider=get_multi_provider())
        
        # Convert outline structure to a format the manuscript formatter can use
        # We'll treat each slide as a 'message' context for restructuring
        synthetic_messages = []
        synthetic_messages.append({"role": "assistant", "content": f"Title: {outline.title}\nSubtitle: {outline.subtitle or ''}"})
        
        for slide in outline.slides:
            slide_text = f"Slide: {slide.get('title')}\n"
            if slide.get("bullets"):
                slide_text += "\n".join([f"- {b}" for b in slide["bullets"]])
            synthetic_messages.append({"role": "assistant", "content": slide_text})
            
        # Structure content with AI
        structured = await formatter.structure_content(synthetic_messages, style="report")
        
        # Build DOCX
        docx_bytes = formatter.build_docx(structured, style="report")
        
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=manuscript_from_slides.docx"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export manuscript from slides: {str(e)}"
        )
