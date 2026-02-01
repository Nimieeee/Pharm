"""
Audio Transcription Service using Mistral Voxtral API
"""

import logging
from typing import Optional, Tuple
from mistralai import Mistral
from app.core.config import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio using Mistral Voxtral API"""
    
    def __init__(self):
        self.client = Mistral(api_key=settings.MISTRAL_API_KEY)
        self.model = "voxtral-mini-latest"
        logger.info(f"✅ TranscriptionService initialized with model: {self.model}")
    
    async def transcribe_audio(
        self,
        audio_content: bytes,
        filename: str,
        language: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Transcribe audio content using Voxtral.
        
        Args:
            audio_content: Raw audio bytes
            filename: Original filename (used to determine format)
            language: Optional language code (e.g., 'en', 'es', 'fr')
            
        Returns:
            Tuple of (transcription_text, error_message)
        """
        try:
            logger.info(f"🎤 Transcribing audio: {filename} ({len(audio_content)} bytes)")
            
            # Prepare the file parameter
            file_param = {
                "content": audio_content,
                "file_name": filename
            }
            
            # Build transcription parameters
            params = {
                "model": self.model,
                "file": file_param
            }
            
            # Add language if specified (improves accuracy)
            if language:
                params["language"] = language
            
            # Call Voxtral API
            response = self.client.audio.transcriptions.complete(**params)
            
            # Extract text from response
            transcription_text = response.text if hasattr(response, 'text') else str(response)
            
            logger.info(f"✅ Transcription complete: {len(transcription_text)} chars")
            return transcription_text, None
            
        except Exception as e:
            error_msg = f"Transcription failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return "", error_msg


# Singleton instance
_transcription_service: Optional[TranscriptionService] = None


def get_transcription_service() -> TranscriptionService:
    """Get or create singleton TranscriptionService"""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
