"""
Lab Report Generation API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
import tempfile
import os
import base64
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.lab_report import LabReportService
from app.services.enhanced_rag import EnhancedRAGService
from app.services.ai import AIService
from supabase import Client

router = APIRouter()
logger = logging.getLogger(__name__)


class LabReportRequest(BaseModel):
    """Request model for lab report generation."""
    experiment_type: str
    conversation_id: str
    instructions: Optional[str] = None


class LabReportResponse(BaseModel):
    """Response model for lab report."""
    status: str
    title: str
    sections: Dict[str, Optional[str]]
    references: List[Dict[str, str]]
    full_report: str
    error: Optional[str] = None


def get_lab_report_service() -> LabReportService:
    """Get lab report service instance."""
    return LabReportService()


def get_rag_service(db: Client = Depends(get_db)) -> EnhancedRAGService:
    """Get RAG service instance."""
    return EnhancedRAGService(db)


def get_ai_service(db: Client = Depends(get_db)) -> AIService:
    """Get AI service instance."""
    from app.services.chat import ChatService
    return AIService(db, ChatService(db))


@router.post("/generate")
async def generate_lab_report(
    experiment_type: str = Form(...),
    conversation_id: str = Form(...),
    instructions: Optional[str] = Form(None),
    data_file: Optional[UploadFile] = File(None),
    methodology_file: Optional[UploadFile] = File(None),
    data_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    lab_service: LabReportService = Depends(get_lab_report_service),
    rag_service: EnhancedRAGService = Depends(get_rag_service),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Generate a structured lab report from experimental data.
    
    - **experiment_type**: Type of experiment (e.g., "Therapeutic Index Determination")
    - **conversation_id**: Conversation to fetch uploaded documents from
    - **instructions**: Optional additional instructions
    - **data_file**: Optional data file (CSV, Excel)
    - **methodology_file**: Optional methodology document (PDF, DOCX)
    - **data_image**: Optional image of data table
    """
    logger.info(f"📝 Lab Report generation requested by {current_user.id}")
    logger.info(f"📊 Experiment Type: {experiment_type}")
    
    try:
        # Collect data context from multiple sources
        data_context_parts = []
        methodology = ""
        
        # 1. Get context from RAG (uploaded documents in conversation)
        try:
            rag_context = await rag_service.get_conversation_context(
                query=f"{experiment_type} experimental data methodology",
                conversation_id=UUID(conversation_id),
                user_id=current_user.id,
                max_chunks=20
            )
            if rag_context and rag_context.strip():
                data_context_parts.append(f"[FROM UPLOADED DOCUMENTS]\n{rag_context}")
                logger.info(f"📄 Retrieved {len(rag_context)} chars from RAG")
        except Exception as e:
            logger.warning(f"⚠️ RAG context fetch failed: {e}")
        
        # 2. Process optional data file
        if data_file and data_file.filename:
            content = await data_file.read()
            if content:
                # For CSV/Excel, include raw content
                try:
                    text_content = content.decode('utf-8')
                    data_context_parts.append(f"[FROM DATA FILE: {data_file.filename}]\n{text_content[:5000]}")
                    logger.info(f"📊 Loaded data file: {data_file.filename}")
                except:
                    # Binary file - save and process
                    pass
        
        # 3. Process optional methodology file
        if methodology_file and methodology_file.filename:
            content = await methodology_file.read()
            if content:
                try:
                    methodology = content.decode('utf-8')[:5000]
                    logger.info(f"📋 Loaded methodology file: {methodology_file.filename}")
                except:
                    methodology = "Methodology document uploaded (binary format)"
        
        # 4. Process optional data image using Pixtral
        if data_image and data_image.filename:
            content = await data_image.read()
            if content:
                try:
                    image_base64 = base64.b64encode(content).decode('utf-8')
                    # Use Pixtral to extract data from image
                    extracted = await ai_service.analyze_image(
                        f"data:image/{data_image.filename.split('.')[-1]};base64,{image_base64}"
                    )
                    if extracted:
                        data_context_parts.append(f"[FROM IMAGE: {data_image.filename}]\n{extracted}")
                        logger.info(f"🖼️ Extracted data from image: {len(extracted)} chars")
                except Exception as e:
                    logger.warning(f"⚠️ Image extraction failed: {e}")
        
        # Combine all data context
        data_context = "\n\n".join(data_context_parts)
        
        if not data_context:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data provided. Please upload data files or ensure documents are uploaded to the conversation."
            )
        
        # Generate the lab report
        result = await lab_service.generate_report(
            experiment_type=experiment_type,
            data_context=data_context,
            methodology=methodology or "Standard laboratory procedures were followed.",
            user_instructions=instructions
        )
        
        logger.info(f"✅ Lab Report generated: {result['status']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Lab Report generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lab report generation failed: {str(e)}"
        )


@router.get("/templates")
async def get_experiment_templates():
    """Get list of common experiment templates."""
    return {
        "templates": [
            {
                "id": "therapeutic_index",
                "name": "Therapeutic Index Determination",
                "description": "Calculate LD50, ED50, and Therapeutic Index using probit analysis"
            },
            {
                "id": "dose_response",
                "name": "Dose-Response Curve",
                "description": "Analyze drug potency and efficacy from dose-response data"
            },
            {
                "id": "enzyme_kinetics",
                "name": "Enzyme Kinetics",
                "description": "Determine Km and Vmax from Michaelis-Menten data"
            },
            {
                "id": "dissolution",
                "name": "Dissolution Study",
                "description": "Drug release profile analysis"
            },
            {
                "id": "stability",
                "name": "Stability Study",
                "description": "Drug degradation kinetics analysis"
            },
            {
                "id": "custom",
                "name": "Custom Experiment",
                "description": "Generate a report for any experiment type"
            }
        ]
    }
