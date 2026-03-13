
import httpx
import logging
from typing import Dict, List, Optional
from app.core.config import settings
from app.utils.rate_limiter import mistral_limiter

logger = logging.getLogger(__name__)

class TranslationService:
    """Service to handle text translation using LLMs"""
    
    def __init__(self):
        self.api_key = settings.MISTRAL_API_KEY
        self.base_url = "https://api.mistral.ai/v1"
        self.model = "mistral-small-latest" # Use small model for speed
        
    async def translate_text(self, text: str, target_language: str) -> Optional[str]:
        """Translate a single text string"""
        if not text or not target_language:
            return None
            
        try:
            # Map codes to full names for better LLM understanding
            lang_map = {
                'en': 'English', 'es': 'Spanish', 'fr': 'French', 
                'de': 'German', 'pt': 'Portuguese', 'zh': 'Chinese',
                'it': 'Italian', 'ru': 'Russian', 'ja': 'Japanese'
            }
            full_lang = lang_map.get(target_language, target_language)
            
            messages = [
                {"role": "system", "content": f"You are a professional medical translator. Translate the following text into {full_lang}. Return ONLY the translated text, no enclosing quotes, no explanations, no markdown (unless original had it). Preserve medical accuracy exactly."},
                {"role": "user", "content": text}
            ]
            
            await mistral_limiter.wait_for_slot()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.1,
                        "max_tokens": 4000
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"Translation failed: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return None
            
    async def translate_batch(self, texts: List[str], target_language: str) -> List[Optional[str]]:
        """Translate a batch of texts (could be optimized to single call, but parallel requests are often faster/simpler)"""
        # For now, simple loop or gather. 
        # Given rate limits, maybe batching into one prompt is better?
        # "Translate the following JSON list..."
        # But that risks parsing errors.
        # Let's use individual calls for reliability but maybe limit concurrency?
        # Actually, let's just stick to individual calls via asyncio.gather in the caller.
        pass

translation_service = TranslationService()
