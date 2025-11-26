"""
Data Analysis Workbench API Endpoints
"""

import os
import tempfile
import shutil
from typing import Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import Client

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.data_workbench import DataWorkbenchService
from app.models.user import User
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class WorkbenchAnalysisRequest(BaseModel):
    """Request model for workbench analysis."""
    style_description: Optional[str] = None


class WorkbenchAnalysisResponse(BaseModel):
    """Response model for workbench analysis."""
    status: str
    image: Optional[str] = None
    statistics: Optional[Dict[str, Any]] = None
    analysis: Optional[str] = None
    style_config: Optional[Dict[str, Any]] = None
    code: Optional[str] = None
    error: Optional[str] = None


def get_workbench_service() -> DataWorkbenchService:
    """Get workbench service instance."""
    return DataWorkbenchService()


@router.post("/analyze", response_model=WorkbenchAnalysisResponse)
async def analyze_data(
    data_file: UploadFile = File(...),
    style_description: Optional[str] = Form(None),
    style_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    workbench_service: DataWorkbenchService = Depends(get_workbench_service)
):
    """
    Analyze uploaded data and generate visualization.
    
    - **data_file**: CSV, Excel, or JSON data file
    - **style_description**: Text description of desired style (e.g., "Nature journal style")
    - **style_image**: Reference image to clone style from
    """
    temp_dir = None
    
    try:
        logger.info(f"📊 Workbench analysis started by user {current_user.id}")
        logger.info(f"📄 File: {data_file.filename}")
        
        # Validate file type
        allowed_extensions = {'.csv', '.xlsx', '.xls', '.json', '.tsv'}
        file_ext = os.path.splitext(data_file.filename or "")[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Create temp directory for files
        temp_dir = tempfile.mkdtemp()
        
        # Save data file
        data_path = os.path.join(temp_dir, data_file.filename or "data.csv")
        content = await data_file.read()
        
        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file uploaded"
            )
        
        with open(data_path, 'wb') as f:
            f.write(content)
        
        logger.info(f"✅ Data file saved: {len(content)} bytes")
        
        # Process style image if provided
        style_image_base64 = None
        if style_image and style_image.filename:
            import base64
            style_content = await style_image.read()
            if style_content:
                style_image_base64 = base64.b64encode(style_content).decode('utf-8')
                logger.info(f"✅ Style image loaded: {len(style_content)} bytes")
        
        # Run analysis
        result = await workbench_service.analyze(
            file_path=data_path,
            file_name=data_file.filename or "data",
            style_description=style_description,
            style_image_base64=style_image_base64
        )
        
        logger.info(f"✅ Analysis complete: status={result['status']}")
        
        return WorkbenchAnalysisResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Workbench error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )
    finally:
        # Cleanup temp files
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


@router.post("/preview")
async def preview_data(
    data_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Get a preview of uploaded data without full analysis.
    
    Returns column names, data types, and sample rows.
    """
    temp_path = None
    
    try:
        import pandas as pd
        
        # Validate file type
        allowed_extensions = {'.csv', '.xlsx', '.xls', '.json', '.tsv'}
        file_ext = os.path.splitext(data_file.filename or "")[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Save to temp file
        content = await data_file.read()
        temp_path = tempfile.mktemp(suffix=file_ext)
        
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Load data
        if file_ext == '.csv':
            df = pd.read_csv(temp_path, nrows=100)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(temp_path, nrows=100)
        elif file_ext == '.json':
            df = pd.read_json(temp_path)
            df = df.head(100)
        elif file_ext == '.tsv':
            df = pd.read_csv(temp_path, sep='\t', nrows=100)
        else:
            df = pd.read_csv(temp_path, nrows=100)
        
        return {
            "filename": data_file.filename,
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "sample": df.head(10).to_dict(orient='records'),
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category']).columns.tolist()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/styles")
async def get_preset_styles():
    """Get list of preset visualization styles."""
    return {
        "styles": [
            {
                "id": "nature",
                "name": "Nature Journal",
                "description": "Clean, minimal style with blue/gray palette",
                "preview_colors": ["#1f77b4", "#7f7f7f", "#2ca02c"]
            },
            {
                "id": "ft",
                "name": "Financial Times",
                "description": "Salmon pink background with dark text",
                "preview_colors": ["#fff1e5", "#990f3d", "#0d7680"]
            },
            {
                "id": "economist",
                "name": "The Economist",
                "description": "Red accent with clean sans-serif",
                "preview_colors": ["#e3120b", "#1a1a1a", "#ffffff"]
            },
            {
                "id": "dark",
                "name": "Dark Mode",
                "description": "Dark background with bright accents",
                "preview_colors": ["#1a1a2e", "#00d4ff", "#ff6b6b"]
            },
            {
                "id": "minimal",
                "name": "Minimal Scientific",
                "description": "White background, subtle grid, grayscale",
                "preview_colors": ["#ffffff", "#333333", "#666666"]
            }
        ]
    }
