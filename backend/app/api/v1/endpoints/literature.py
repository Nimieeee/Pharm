from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
import io
import httpx

from app.core.security import get_current_user
from app.models.user import User
from app.services.literature_service import get_literature_service, LiteratureService

router = APIRouter()

@router.get("/search")
async def search_literature(
    query: str = Query(..., description="Search query"),
    max_results: int = Query(20, ge=1, le=50, description="Maximum results"),
    year_from: Optional[int] = Query(None, description="Filter from year"),
    year_to: Optional[int] = Query(None, description="Filter to year"),
    current_user: User = Depends(get_current_user),
    service: LiteratureService = Depends(get_literature_service)
):
    """Unified search across PubMed and Semantic Scholar"""
    try:
        results = await service.search_all(query, max_results, year_from, year_to)
        return {
            "query": query,
            "count": len(results),
            "results": results,
            "filters": {"year_from": year_from, "year_to": year_to}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/pdf/link")
async def get_pdf_link(
    pmid: Optional[str] = Query(None),
    doi: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: LiteratureService = Depends(get_literature_service)
):
    """Get a direct PDF download link for a PMID or DOI"""
    if not pmid and not doi:
        raise HTTPException(status_code=400, detail="Either pmid or doi must be provided")
        
    link = await service.get_pdf_link(pmid=pmid, doi=doi)
    if not link:
        raise HTTPException(status_code=404, detail="Open Access PDF not found")
    return {"pdf_url": link}

@router.get("/pdf/download")
async def download_pdf(
    pmid: Optional[str] = Query(None),
    doi: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    service: LiteratureService = Depends(get_literature_service)
):
    """Proxy download PDF bytes"""
    link = await service.get_pdf_link(pmid=pmid, doi=doi)
    if not link:
        raise HTTPException(status_code=404, detail="Open Access PDF not found")
    
    try:
        pdf_bytes = await service.fetch_pdf_bytes(link)
        filename = f"PDF_{pmid or doi}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch PDF: {str(e)}")
