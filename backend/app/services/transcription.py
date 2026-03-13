"""
Audio Transcription Service using Mistral Voxtral API

NOTE: Uses HTTP API directly as mistralai SDK doesn't have audio namespace.
"""

import logging
import httpx
import io
from typing import Optional, Tuple
from app.core.config import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio using Mistral Voxtral API"""

    def __init__(self):
        if not settings.MISTRAL_API_KEY:
            logger.warning("MISTRAL_API_KEY not found in environment for Audio Transcription")
            self.api_key = None
        else:
            self.api_key = settings.MISTRAL_API_KEY
        self.model = "voxtral-mini-latest"
        self.base_url = "https://api.mistral.ai/v1"
        logger.info(f"✅ TranscriptionService initialized with model: {self.model}")

    async def transcribe_audio(
        self,
        audio_content: bytes,
        filename: str,
        language: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        Transcribe audio content using Mistral Voxtral API.

        Args:
            audio_content: Raw audio bytes
            filename: Original filename (used to determine format)
            language: Optional language code (e.g., 'en', 'es', 'fr')

        Returns:
            Tuple of (transcription_text, error_message)
        """
        if not self.api_key:
            return "", "Mistral API key not configured"

        try:
            logger.info(f"🎤 Transcribing audio: {filename} ({len(audio_content)} bytes)")

            # Correct way to send multipart data in httpx
            # files parameter handles multipart form data automatically
            files = {
                "file": (filename or "audio.webm", io.BytesIO(audio_content), "audio/webm")
            }
            data = {
                "model": self.model
            }
            if language:
                data["language"] = language

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    data=data,
                    files=files
                )

                if response.status_code != 200:
                    error_text = response.text[:500] if response.text else "Unknown error"
                    raise Exception(f"Mistral API error ({response.status_code}): {error_text}")

                result = response.json()
                transcription_text = result.get("text", "")

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
