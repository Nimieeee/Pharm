from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from typing import List, Optional
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import io

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.models.user import User
from supabase import Client

router = APIRouter()


class ADMETAnalysisRequest(BaseModel):
    """Request model for ADMET analysis"""
    smiles: str
    include_svg: bool = True


def get_admet_service(db: Client = Depends(get_db)):
    """Get ADMET service with dependency injection"""
    from app.services.admet_service import ADMETService
    return ADMETService(db)


@router.post("/batch")
async def analyze_batch(
    file: UploadFile = File(None),
    smiles_list: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_optional_user),
    admet_service = Depends(get_admet_service)
):
    """
    Batch ADMET analysis.
    Accepts: SDF file upload OR JSON string of SMILES array.
    """
    try:
        import json
        smiles_to_analyze = []
        
        if file:
            content = await file.read()
            smiles_to_analyze = await admet_service.extract_smiles_from_sdf(content)
        elif smiles_list:
            smiles_to_analyze = json.loads(smiles_list)
            
        if not smiles_to_analyze:
            raise HTTPException(400, "No SMILES provided for analysis")

        # Limit batch size to prevent timeouts
        if len(smiles_to_analyze) > 20:
             smiles_to_analyze = smiles_to_analyze[:20]
             
        results = await admet_service.analyze_batch(smiles_to_analyze)
        
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch ADMET analysis failed: {str(e)}"
        )


@router.post("/analyze")
async def analyze_molecule(
    request: ADMETAnalysisRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    admet_service = Depends(get_admet_service)
):
    """
    Full ADMET analysis for a molecule.
    
    - **smiles**: SMILES string of the molecule
    - **include_svg**: Whether to include structure SVG (default: True)
    - Returns: Markdown report with ADMET predictions
    """
    try:
        report = await admet_service.generate_report(request.smiles)
        
        return {
            "success": True,
            "smiles": request.smiles,
            "report": report,
            "include_svg": request.include_svg
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ADMET analysis failed: {str(e)}"
        )


@router.get("/svg")
async def get_molecule_svg(
    smiles: str = Query(..., description="SMILES string"),
    admet_service = Depends(get_admet_service)
):
    """
    Generate SVG for molecule structure.
    
    - **smiles**: SMILES string
    - Returns: SVG string
    """
    try:
        svg = await admet_service.get_svg(smiles)
        
        if not svg:
            raise HTTPException(400, "Failed to generate SVG")
        
        return Response(content=svg, media_type="image/svg+xml")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SVG generation failed: {str(e)}"
        )


@router.get("/export")
async def export_admet_csv(
    smiles: str = Query(..., description="SMILES string"),
    admet_service = Depends(get_admet_service)
):
    """
    Export ADMET results as CSV.
    
    - **smiles**: SMILES string
    - Returns: CSV file download
    """
    try:
        # Get full ADMET data
        admet_data = await admet_service.predict_admet(smiles)
        
        # Convert to CSV
        csv_content = admet_service.export_as_csv(admet_data)
        
        # Return as download
        file_stream = io.BytesIO(csv_content.encode('utf-8'))
        file_stream.seek(0)
        
        return StreamingResponse(
            file_stream,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=admet_{smiles[:20]}.csv"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CSV export failed: {str(e)}"
        )


@router.get("/wash")
async def wash_molecule(
    smiles: str = Query(..., description="SMILES string"),
    admet_service = Depends(get_admet_service)
):
    """
    Standardize SMILES via ADMETlab washmol.
    
    - **smiles**: Input SMILES
    - Returns: Standardized SMILES
    """
    try:
        washed = await admet_service.wash_molecule(smiles)
        
        return {
            "original": smiles,
            "washed": washed,
            "changed": smiles != washed
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Molecule washing failed: {str(e)}"
        )
