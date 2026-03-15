from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio, json, io, uuid

from app.core.security import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.core.container import get_container
from supabase import Client

router = APIRouter()

# --- Request/Response Models ---

class DocOutlineRequest(BaseModel):
    topic: str
    doc_type: str = "report"  # report, manuscript, whitepaper, case_report
    context: Optional[str] = None
    conversation_id: Optional[str] = None

class DocGenerateRequest(BaseModel):
    outline: Dict[str, Any]
    doc_type: str = "report"

# --- Storage for in-progress jobs ---
doc_jobs: dict = {}  # job_id -> {"status": ..., "docx_bytes": ..., "queue": asyncio.Queue}

# --- Endpoints ---

@router.post("/outline")
async def generate_doc_outline(
    request: DocOutlineRequest,
    current_user: User = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Step 1: Generate editable document outline"""
    try:
        from app.services.doc_service import get_doc_service
        
        # Get multi_provider from container
        container = get_container(db)
        ai_service = container.get('ai_service')
        multi_provider = ai_service.multi_provider
        
        doc_service = get_doc_service(multi_provider)
        
        # Pull conversation context if provided
        context = None
        if request.conversation_id:
            from app.services.enhanced_rag import EnhancedRAGService
            rag = EnhancedRAGService(db)
            context = await rag.get_conversation_context(
                query=request.topic,
                conversation_id=request.conversation_id,
                user_id=current_user.id
            )
        
        outline = await doc_service.generate_outline(
            topic=request.topic,
            doc_type=request.doc_type,
            context=context or request.context
        )
        
        return outline
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate outline: {str(e)}"
        )

@router.post("/generate")
async def generate_document(
    request: DocGenerateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Step 2: Start background DOCX generation. Returns job_id."""
    try:
        job_id = str(uuid.uuid4())
        doc_jobs[job_id] = {
            "status": "started", 
            "docx_bytes": None, 
            "queue": asyncio.Queue(),
            "message": "Initializing..."
        }
        
        background_tasks.add_task(run_doc_generation, job_id, request)
        return {"job_id": job_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def run_doc_generation(job_id: str, request: DocGenerateRequest, db: Client = None):
    from app.services.doc_service import get_doc_service
    
    # Get multi_provider from container if db provided
    multi_provider = None
    if db:
        try:
            container = get_container(db)
            ai_service = container.get('ai_service')
            multi_provider = ai_service.multi_provider
        except Exception:
            pass
    
    doc_service = get_doc_service(multi_provider)
    
    async def on_progress(data):
        doc_jobs[job_id].update({
            "message": data.get("message", "")
        })
        await doc_jobs[job_id]["queue"].put(data)
    
    try:
        docx_bytes = await doc_service.generate_document(
            outline=request.outline,
            on_progress=on_progress
        )
        doc_jobs[job_id]["docx_bytes"] = docx_bytes
        doc_jobs[job_id]["status"] = "complete"
        await doc_jobs[job_id]["queue"].put({"status": "complete", "job_id": job_id})
    except Exception as e:
        doc_jobs[job_id]["status"] = "error"
        await doc_jobs[job_id]["queue"].put({"status": "error", "error": str(e)})

@router.get("/status/{job_id}")
async def get_doc_status(job_id: str):
    """SSE endpoint for document generation progress"""
    if job_id not in doc_jobs:
        raise HTTPException(404, "Job not found")

    async def event_generator():
        queue = doc_jobs[job_id]["queue"]
        while True:
            data = await queue.get()
            yield {"event": "message", "data": json.dumps(data)}
            if data.get("status") in ["complete", "error"]:
                break
    
    return EventSourceResponse(event_generator())

@router.get("/download/{job_id}")
async def download_document(job_id: str, current_user: User = Depends(get_current_user)):
    """Download generated DOCX"""
    job = doc_jobs.get(job_id)
    if not job or not job["docx_bytes"]:
        raise HTTPException(404, "Document job not found or not complete")
    
    return StreamingResponse(
        io.BytesIO(job["docx_bytes"]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=benchside_doc_{job_id[:8]}.docx"}
    )
