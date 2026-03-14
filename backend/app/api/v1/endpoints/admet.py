from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from typing import List, Optional
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
import io
import urllib.parse

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from supabase import Client

router = APIRouter()


class ADMETAnalysisRequest(BaseModel):
    """Request model for ADMET analysis"""
    smiles: str
    include_svg: bool = True


class BatchExportRequest(BaseModel):
    """Request model for batch CSV export"""
    results: List[dict]


def get_admet_service(db: Client = Depends(get_db)):
    """Get ADMET service with dependency injection"""
    from app.services.admet_service import ADMETService
    return ADMETService(db)


@router.post("/batch")
async def analyze_batch(
    file: UploadFile = File(None),
    smiles_list: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    admet_service = Depends(get_admet_service)
):
    """
    Batch ADMET analysis.
    Accepts: SDF file upload OR JSON string of SMILES array.
    """
    try:
        import json
        molecules = []
        
        if file:
            content = await file.read()
            # extract_smiles_from_sdf returns list of SMILES or dicts
            molecules = await admet_service.extract_smiles_from_sdf(content)
        elif smiles_list:
            raw = json.loads(smiles_list)
            # Accept both ["SMILES1", "SMILES2"] and [{"smiles": "...", "name": "..."}]
            molecules = [
                {"smiles": s, "name": f"Molecule {i+1}"} if isinstance(s, str) else s
                for i, s in enumerate(raw)
            ]
            
        if not molecules:
            raise HTTPException(400, "No SMILES provided for analysis")

        # Cap at 100 for now (up from 20), warn user in response
        total = len(molecules)
        capped = molecules[:100]
        
        results = await admet_service.analyze_batch_structured(capped)
        
        return {
            "success": True,
            "count": len(results),
            "total_submitted": total,
            "capped_at": 100 if total > 100 else None,
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
    current_user: User = Depends(get_current_user),
    admet_service = Depends(get_admet_service)
):
    """
    Full ADMET analysis for a molecule.
    
    - **smiles**: SMILES string of the molecule
    - **include_svg**: Whether to include structure SVG (default: True)
    - Returns: Structured JSON with ADMET predictions + legacy markdown
    """
    try:
        # 1. Get raw predictions (dict with 46 keys)
        admet_data = await admet_service.predict_admet(request.smiles)
        
        # 2. Get SVG
        svg = None
        if request.include_svg:
            try:
                svg = await admet_service.get_svg(request.smiles)
            except Exception:
                pass
        
        # 3. Get AI interpretation
        ai_interpretation = None
        try:
            ai_interpretation = await admet_service._generate_ai_interpretation(admet_data)
        except Exception:
            pass
        
        # 4. Build structured categories from raw data
        categories = admet_service.processor.build_structured_categories(admet_data)
        
        # 5. Also generate markdown for legacy support/copying
        report_md = admet_service.processor.format_report(admet_data, svg, ai_interpretation)
        
        return {
            "success": True,
            "smiles": request.smiles,
            "svg": svg,
            "engine": admet_data.get("_engine", "Unknown"),
            "categories": categories,
            "ai_interpretation": ai_interpretation,
            "report_markdown": report_md,
            "report": report_md # alias for backward compatibility
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ADMET analysis failed: {str(e)}"
        )


@router.get("/svg")
async def get_molecule_svg(
    smiles: str = Query(..., description="SMILES string (URL-encoded)"),
    admet_service = Depends(get_admet_service)
):
    """
    Generate SVG for molecule structure.

    - **smiles**: SMILES string (URL-encoded, e.g., %3D for =)
    - Returns: SVG string
    """
    try:
        # Decode URL-encoded SMILES
        decoded_smiles = urllib.parse.unquote(smiles)

        svg = await admet_service.get_svg(decoded_smiles)

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
        csv_content = await admet_service.export_as_csv(admet_data)
        
        # Return as download
        file_stream = io.BytesIO(csv_content.encode('utf-8'))
        file_stream.seek(0)
        
        # Determine filename
        mol_name = admet_data.get("molecule_name") or f"admet_{smiles[:20]}"
        filename = f"{mol_name}.csv".replace(" ", "_")
        
        return StreamingResponse(
            file_stream,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"CSV export failed: {str(e)}"
        )


@router.post("/export/batch")
async def export_batch_csv(
    request: BatchExportRequest,
    current_user: User = Depends(get_current_user),
    admet_service = Depends(get_admet_service)
):
    """
    Export batch ADMET results as a single CSV.
    
    - **results**: List of structured analysis results
    - Returns: CSV file download
    """
    try:
        # Use the already implemented format_batch_csv method
        csv_content = admet_service.processor.format_batch_csv(request.results)
        
        # Return as download
        file_stream = io.BytesIO(csv_content.encode('utf-8'))
        file_stream.seek(0)
        
        filename = f"admet_batch_{len(request.results)}_compounds.csv"
        
        return StreamingResponse(
            file_stream,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Batch CSV export failed: {str(e)}"
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
