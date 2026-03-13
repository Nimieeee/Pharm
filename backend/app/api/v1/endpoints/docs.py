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

class DocOutlineRequest(BaseModel):
    topic: str
    doc_type: str = "report"  # report, manuscript, whitepaper, case_report
    context: Optional[str] = None
    conversation_id: Optional[str] = None

class DocGenerateRequest(BaseModel):
    outline: Dict[str, Any]
    doc_type: str = "report"

# --- Storage for in-progress jobs ---
doc_jobs: dict = {}  # job_id -> {"status": ..., "docx_bytes": ...}

# --- Endpoints ---

@router.post("/outline")
async def generate_doc_outline(
    request: DocOutlineRequest,
    current_user: User = Depends(get_current_user)
):
    """Step 1: Generate editable document outline"""
    try:
        from app.services.doc_service import get_doc_service
        
        doc_service = get_doc_service()
        
        # Pull conversation context if provided
        context = None
        if request.conversation_id:
            from app.services.enhanced_rag import EnhancedRAGService
            from app.core.database import get_db
            rag = EnhancedRAGService(get_db())
            context = await rag.get_conversation_context(request.conversation_id)
        
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
    current_user: User = Depends(get_current_user)
):
    """Step 2: Generate DOCX from approved outline. Returns SSE progress."""
    try:
        from app.services.doc_service import get_doc_service
        
        doc_service = get_doc_service()
        job_id = str(uuid.uuid4())
        doc_jobs[job_id] = {"status": "started", "docx_bytes": None}
        
        async def event_generator():
            async def on_progress(data):
                yield {"event": "progress", "data": json.dumps(data)}
            
            try:
                docx_bytes = await doc_service.generate_document(
                    outline=request.outline,
                    on_progress=on_progress
                )
                doc_jobs[job_id]["docx_bytes"] = docx_bytes
                doc_jobs[job_id]["status"] = "complete"
                yield {"event": "complete", "data": json.dumps({"job_id": job_id})}
            except Exception as e:
                doc_jobs[job_id]["status"] = "error"
                yield {"event": "error", "data": json.dumps({"error": str(e)})}
        
        return EventSourceResponse(event_generator())
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate document: {str(e)}"
        )

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
