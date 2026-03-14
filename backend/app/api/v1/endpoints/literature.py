from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Optional
import io
import httpx

from app.core.security import get_current_user
from app.models.user import User
from app.services.literature_service import get_literature_service, LiteratureService

router = APIRouter()

@router.get("/pdf/link/{pmid}")
async def get_pdf_link(
    pmid: str,
    current_user: User = Depends(get_current_user),
    service: LiteratureService = Depends(get_literature_service)
):
    """Get a direct PDF download link for a PMID"""
    link = await service.get_pdf_link(pmid)
    if not link:
        raise HTTPException(status_code=404, detail="Open Access PDF not found for this article")
    return {"pdf_url": link}

@router.get("/pdf/download/{pmid}")
async def download_pdf(
    pmid: str,
    current_user: User = Depends(get_current_user),
    service: LiteratureService = Depends(get_literature_service)
):
    """Proxy download PDF bytes for a PMID"""
    link = await service.get_pdf_link(pmid)
    if not link:
        raise HTTPException(status_code=404, detail="Open Access PDF not found")
    
    try:
        pdf_bytes = await service.fetch_pdf_bytes(link)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=PMID_{pmid}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch PDF: {str(e)}")
