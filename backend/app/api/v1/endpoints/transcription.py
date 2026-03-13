"""
Audio Transcription API Endpoint
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.transcription import get_transcription_service
from app.core.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audio", tags=["audio"])


class TranscriptionResponse(BaseModel):
    """Response model for transcription"""
    success: bool
    text: str
    error: Optional[str] = None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe audio file to text using Voxtral.
    
    Supported formats: MP3, WAV, WebM, OGG, M4A
    Max duration: 30 minutes
    """
    try:
        # Validate file type
        allowed_types = {
            "audio/webm", "audio/mp3", "audio/mpeg", "audio/wav", 
            "audio/ogg", "audio/m4a", "audio/x-m4a", "audio/mp4"
        }
        
        content_type = file.content_type or ""
        if content_type not in allowed_types and not content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {content_type}. Supported: MP3, WAV, WebM, OGG, M4A"
            )
        
        # Read audio content
        audio_content = await file.read()
        
        # Validate size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(audio_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"Audio file too large. Max size: 50MB"
            )
        
        logger.info(f"🎤 Transcription request from user {current_user.id}: {file.filename} ({len(audio_content)} bytes)")
        
        # Get transcription service and transcribe
        service = get_transcription_service()
        text, error = await service.transcribe_audio(
            audio_content=audio_content,
            filename=file.filename or "audio.webm",
            language=language
        )
        
        if error:
            return TranscriptionResponse(success=False, text="", error=error)
        
        return TranscriptionResponse(success=True, text=text)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
