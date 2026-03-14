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

# Import calculators for synthetic accessibility
from app.services.sas_service import sas_calculator
from app.services.gasa_service import gasa_predictor
from app.services.simple_gasa_service import simple_gasa_predictor

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
    page: int = Form(1),
    page_size: int = Form(50),
    current_user: User = Depends(get_current_user),
    admet_service = Depends(get_admet_service)
):
    """
    Batch ADMET analysis with pagination.
    Accepts: SDF file upload OR JSON string of SMILES array.

    - **page**: Page number (1-indexed, default: 1)
    - **page_size**: Results per page (default: 50, max: 100)
    """
    try:
        import json
        molecules = []

        if file:
            content = await file.read()
            molecules = await admet_service.extract_smiles_from_sdf(content)
        elif smiles_list:
            raw = json.loads(smiles_list)
            molecules = [
                {"smiles": s, "name": f"Molecule {i+1}"} if isinstance(s, str) else s
                for i, s in enumerate(raw)
            ]

        if not molecules:
            raise HTTPException(400, "No SMILES provided for analysis")

        # Pagination
        total = len(molecules)
        page_size = min(page_size, 100)  # Max 100 per page
        total_pages = (total + page_size - 1) // page_size
        page = max(1, min(page, total_pages))

        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total)
        capped = molecules[start_idx:end_idx]

        results = await admet_service.analyze_batch_structured(capped)

        # Add SAS and GASA scores to each result
        for result in results:
            smiles = result.get('smiles', '')
            if smiles:
                # Calculate SAS
                sas_result = sas_calculator.calculate(smiles)
                if sas_result:
                    result['synthetic_accessibility'] = sas_result

                # Calculate GASA (if available)
                gasa_result = gasa_predictor.predict_single(smiles)
                if gasa_result and result.get('synthetic_accessibility'):
                    result['synthetic_accessibility'].update({
                        'gasa_prediction': gasa_result['prediction'],
                        'gasa_easy_probability': gasa_result['easy_probability'],
                        'gasa_hard_probability': gasa_result['hard_probability'],
                        'gasa_interpretation': gasa_result['interpretation']
                    })

                    # Add consensus
                    sas_easy = result['synthetic_accessibility']['sas_score'] <= 5.0
                    gasa_easy = gasa_result['prediction'] == 0
                    result['synthetic_accessibility']['consensus'] = (
                        "Both methods agree: Easy to synthesize" if (sas_easy and gasa_easy) else
                        "Both methods agree: Difficult to synthesize" if (not sas_easy and not gasa_easy) else
                        "Mixed results: Check both scores"
                    )

        return {
            "success": True,
            "count": len(results),
            "total_submitted": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
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

        # 3. Calculate SAS score
        sas_result = sas_calculator.calculate(request.smiles)

        # 4. Calculate GASA score (use simple predictor as fallback)
        gasa_result = gasa_predictor.predict_single(request.smiles)
        if not gasa_result:
            # Fallback to simple GASA if DGL-based fails
            gasa_result = simple_gasa_predictor.predict_single(request.smiles)

        # 5. Get AI interpretation
        ai_interpretation = None
        try:
            ai_interpretation = await admet_service._generate_ai_interpretation(admet_data)
        except Exception:
            pass

        # 6. Build combined synthetic accessibility result
        synthetic_accessibility = sas_result
        if gasa_result:
            synthetic_accessibility['gasa_prediction'] = gasa_result['prediction']
            synthetic_accessibility['gasa_easy_probability'] = gasa_result['easy_probability']
            synthetic_accessibility['gasa_hard_probability'] = gasa_result['hard_probability']
            synthetic_accessibility['gasa_interpretation'] = gasa_result['interpretation']

            # Consensus scoring
            sas_easy = sas_result['sas_score'] <= 5.0 if sas_result else False
            gasa_easy = gasa_result['prediction'] == 0
            synthetic_accessibility['consensus'] = (
                "Both methods agree: Easy to synthesize" if (sas_easy and gasa_easy) else
                "Both methods agree: Difficult to synthesize" if (not sas_easy and not gasa_easy) else
                "Mixed results: Check both scores"
            )

        # 7. Build structured categories from raw data
        categories = admet_service.processor.build_structured_categories(admet_data)

        # 8. Generate markdown report WITH synthetic accessibility included
        report_md = admet_service.processor.format_report(admet_data, svg, ai_interpretation, synthetic_accessibility)

        return {
            "success": True,
            "smiles": request.smiles,
            "svg": svg,
            "engine": admet_data.get("_engine", "Unknown"),
            "categories": categories,
            "ai_interpretation": ai_interpretation,
            "report_markdown": report_md,
            "report": report_md, # alias for backward compatibility
            "synthetic_accessibility": synthetic_accessibility
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

    - **smiles**: SMILES string (auto-detects URL encoding)
    - Returns: SVG string
    """
    try:
        # Auto-detect and decode URL-encoded SMILES
        # Check if smiles contains % (URL-encoded)
        if '%' in smiles:
            decoded_smiles = urllib.parse.unquote(smiles)
        else:
            decoded_smiles = smiles

        svg = await admet_service.get_svg(decoded_smiles)

        if not svg:
            # Return placeholder SVG for invalid SMILES
            return Response(
                content='<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300"><text x="50%" y="50%" text-anchor="middle" fill="#999">Invalid SMILES</text></svg>',
                media_type="image/svg+xml"
            )

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


@router.get("/export/pdf")
async def export_admet_pdf(
    smiles: str = Query(..., description="SMILES string"),
    admet_service = Depends(get_admet_service)
):
    """
    Export ADMET results as PDF.
    """
    try:
        # Get full ADMET data
        admet_data = await admet_service.predict_admet(smiles)
        
        # Calculate SAS score and AI interpretation as they are needed for the report
        from app.services.sas_service import sas_calculator
        admet_data["synthetic_accessibility"] = sas_calculator.calculate(smiles)
        admet_data["ai_interpretation"] = await admet_service._generate_ai_interpretation(admet_data)
        
        # Generate PDF
        pdf_content = await admet_service.generate_pdf(admet_data)
        
        # Return as download
        file_stream = io.BytesIO(pdf_content)
        file_stream.seek(0)
        
        mol_name = admet_data.get("molecule_name") or f"admet_{smiles[:10]}"
        filename = f"{mol_name}.pdf".replace(" ", "_")
        
        return StreamingResponse(
            file_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF export failed: {str(e)}"
        )


@router.get("/export/docx")
async def export_admet_docx(
    smiles: str = Query(..., description="SMILES string"),
    admet_service = Depends(get_admet_service)
):
    """
    Export ADMET results as Word document.
    """
    try:
        # Get full ADMET data
        admet_data = await admet_service.predict_admet(smiles)
        
        # Calculate SAS score and AI interpretation
        from app.services.sas_service import sas_calculator
        admet_data["synthetic_accessibility"] = sas_calculator.calculate(smiles)
        admet_data["ai_interpretation"] = await admet_service._generate_ai_interpretation(admet_data)
        
        # Generate DOCX
        docx_content = await admet_service.generate_docx(admet_data)
        
        # Return as download
        file_stream = io.BytesIO(docx_content)
        file_stream.seek(0)
        
        mol_name = admet_data.get("molecule_name") or f"admet_{smiles[:10]}"
        filename = f"{mol_name}.docx".replace(" ", "_")
        
        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Word export failed: {str(e)}"
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
