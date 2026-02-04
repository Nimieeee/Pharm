"""
Translation Service
Handles background translation of messages to all supported languages
Uses async background tasks to respect rate limits (1 req/s)
"""

import asyncio
import json
from typing import Dict, Optional, List
from uuid import UUID
import httpx
from supabase import Client

from app.core.config import settings
from app.utils.rate_limiter import mistral_limiter

# Supported languages
SUPPORTED_LANGUAGES = ['en', 'es', 'fr', 'de', 'pt', 'zh']

LANGUAGE_NAMES = {
    'en': 'English',
    'es': 'Spanish', 
    'fr': 'French',
    'de': 'German',
    'pt': 'Portuguese',
    'zh': 'Chinese'
}


class TranslationService:
    """Service for translating messages to all supported languages"""
    
    def __init__(self, db: Client):
        self.db = db
        self.mistral_api_key = settings.MISTRAL_API_KEY
        self.mistral_base_url = "https://api.mistral.ai/v1"
    
    async def translate_text(self, text: str, target_language: str, source_language: str = 'en') -> Optional[str]:
        """
        Translate text to a target language using NVIDIA Kimi (primary) or Mistral (fallback)
        
        Args:
            text: Text to translate
            target_language: Target language code (e.g., 'es', 'fr')
            source_language: Source language code (default 'en')
            
        Returns:
            Translated text or None if failed
        """
        if target_language == source_language:
            return text
            
        if not text or text.strip() == "" or "No response generated" in text:
            return text
            
        target_name = LANGUAGE_NAMES.get(target_language, target_language)
        source_name = LANGUAGE_NAMES.get(source_language, source_language)
        
        messages = [
            {
                "role": "system",
                "content": f"You are a professional translator. Translate the following text from {source_name} to {target_name}. Preserve all formatting, markdown, and special characters. Only output the translation, nothing else."
            },
            {
                "role": "user", 
                "content": text
            }
        ]

        # 1. Try NVIDIA Kimi K2.5 (Primary - Using STREAMING which works on VPS)
        # REVERTED: Kimi streaming is too slow for backfill. Using Mistral only.
        # if settings.NVIDIA_API_KEY:
        #     try:
        #         NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
        #         NVIDIA_MODEL = "moonshotai/kimi-k2.5"
                
        #         headers = {
        #             "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        #             "Accept": "text/event-stream",
        #             "Content-Type": "application/json"
        #         }
                
        #         payload = {
        #             "model": NVIDIA_MODEL,
        #             "messages": messages,
        #             "temperature": 0.1,
        #             "max_tokens": 4096,
        #             "stream": True  # Use streaming to avoid timeout
        #         }
                
        #         async with httpx.AsyncClient(timeout=120.0) as client:
        #             async with client.stream(
        #                 "POST",
        #                 NVIDIA_URL,
        #                 headers=headers,
        #                 json=payload
        #             ) as response:
        #                 if response.status_code == 200:
        #                     translated_text = ""
        #                     async for line in response.aiter_lines():
        #                         if line.startswith("data: "):
        #                             data = line[6:]
        #                             if data == "[DONE]":
        #                                 break
        #                             try:
        #                                 chunk = json.loads(data)
        #                                 if chunk.get("choices") and len(chunk["choices"]) > 0:
        #                                     delta = chunk["choices"][0].get("delta", {})
        #                                     content = delta.get("content")
        #                                     if content:
        #                                         translated_text += content
        #                             except json.JSONDecodeError:
        #                                 continue
                            
        #                     if translated_text:
        #                         print(f"✅ [Kimi] Translated to {target_language}")
        #                         return translated_text
        #                 else:
        #                     error_text = await response.aread()
        #                     print(f"⚠️ Kimi Translation failed ({response.status_code}): {error_text[:100]}, falling back to Mistral...")
                            
        #     except Exception as e:
        #         print(f"⚠️ Kimi Error: {e}, falling back to Mistral...")
        if not self.mistral_api_key:
            print(f"⚠️ Translation skipped: No Mistral API key")
            return None
        
        try:
            # Wait for rate limiter
            await mistral_limiter.wait_for_slot()
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.mistral_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.mistral_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "mistral-large-latest",
                        "messages": messages,
                        "temperature": 0.1,
                        "max_tokens": 8000
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("choices") and len(result["choices"]) > 0:
                        translated = result["choices"][0]["message"]["content"]
                        print(f"✅ [Mistral] Translated to {target_language}")
                        return translated
                else:
                    print(f"❌ Translation API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"❌ Translation error: {e}")
            return None
    
    async def translate_to_all_languages(
        self, 
        text: str, 
        source_language: str = 'en',
        exclude_source: bool = True
    ) -> Dict[str, str]:
        """
        Translate text to all supported languages sequentially (rate limited)
        
        Args:
            text: Text to translate
            source_language: Source language code
            exclude_source: If True, don't translate to source language
            
        Returns:
            Dict mapping language codes to translations
        """
        translations = {source_language: text}  # Original text
        
        target_languages = [lang for lang in SUPPORTED_LANGUAGES if lang != source_language]
        
        for target_lang in target_languages:
            translated = await self.translate_text(text, target_lang, source_language)
            if translated:
                translations[target_lang] = translated
            # Rate limiting is handled inside translate_text
            
        return translations
    
    async def queue_message_translation(
        self,
        message_id: UUID,
        content: str,
        source_language: str = 'en'
    ):
        """
        Queue background translation for a message
        Translations are stored in the database as they complete
        """
        print(f"📝 Queueing translations for message {message_id} (Source: '{source_language}')")
        
        # Run translations in background
        asyncio.create_task(
            self._translate_and_store_message(message_id, content, source_language)
        )
    
    async def _translate_and_store_message(
        self,
        message_id: UUID,
        content: str,
        source_language: str
    ):
        """Background task to translate message and store results"""
        try:
            translations = await self.translate_to_all_languages(content, source_language)
            
            # Update message in database with translations
            self.db.table("messages").update({
                "translations": json.dumps(translations)
            }).eq("id", str(message_id)).execute()
            
            print(f"✅ Stored translations for message {message_id}: {list(translations.keys())}")
            
        except Exception as e:
            print(f"❌ Failed to store translations for message {message_id}: {e}")
    
    async def queue_conversation_title_translation(
        self,
        conversation_id: UUID,
        title: str,
        source_language: str = 'en'
    ):
        """
        Queue background translation for a conversation title
        """
        print(f"📝 Queueing title translations for conversation {conversation_id}")
        
        asyncio.create_task(
            self._translate_and_store_title(conversation_id, title, source_language)
        )
    
    async def _translate_and_store_title(
        self,
        conversation_id: UUID,
        title: str,
        source_language: str
    ):
        """Background task to translate title and store results"""
        try:
            translations = await self.translate_to_all_languages(title, source_language)
            
            # Update conversation in database with title translations
            self.db.table("conversations").update({
                "title_translations": json.dumps(translations)
            }).eq("id", str(conversation_id)).execute()
            
            print(f"✅ Stored title translations for conversation {conversation_id}")
            
        except Exception as e:
            print(f"❌ Failed to store title translations: {e}")
    
    async def get_message_in_language(
        self,
        message_id: UUID,
        language: str
    ) -> Optional[str]:
        """
        Get message content in specified language
        Returns None if translation not available
        """
        try:
            result = self.db.table("messages").select(
                "content", "translations"
            ).eq("id", str(message_id)).single().execute()
            
            if result.data:
                translations = result.data.get("translations")
                if translations:
                    if isinstance(translations, str):
                        translations = json.loads(translations)
                    if language in translations:
                        return translations[language]
                        
                # Fallback to original content
                return result.data.get("content")
                
        except Exception as e:
            print(f"❌ Error getting message translation: {e}")
            return None
