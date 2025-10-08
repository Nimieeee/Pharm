"""
Cohere Embeddings Service
Handles embedding generation using Cohere API with caching
Supports both text and image embeddings
Much faster than Mistral - 100 requests/minute on free tier
Uses direct HTTP calls to avoid dependency conflicts
"""

import asyncio
import base64
import hashlib
import httpx
import json
import logging
import time
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from cachetools import TTLCache
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingCacheEntry:
    """Cache entry for embeddings"""
    def __init__(self, embedding: List[float], model_version: str):
        self.embedding = embedding
        self.model_version = model_version
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=settings.EMBEDDING_CACHE_TTL)


class CohereEmbeddingsService:
    """Service for generating embeddings using Cohere API"""
    
    def __init__(self):
        self.cohere_api_key = settings.COHERE_API_KEY
        self.cohere_base_url = "https://api.cohere.ai/v1"
        self.text_model_name = "embed-english-v3.0"
        self.multimodal_model_name = "embed-english-v3.0"  # Same model handles both
        self.embedding_dimensions = 1024  # Cohere embed-english-v3.0 dimensions
        self.cache = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "api_calls": 0,
            "total_requests": 0,
            "image_requests": 0,
            "text_requests": 0
        }
        # Rate limiting: Cohere free tier allows 100 requests per minute
        self.last_api_call_time = 0
        self.min_time_between_calls = 0.6  # 0.6 seconds = 100 requests/minute
        
        # Check API key
        if not self.cohere_api_key:
            logger.warning("⚠️  COHERE_API_KEY not set - embeddings will fail")
        else:
            logger.info("✅ Cohere embeddings service initialized (direct HTTP)")
        
        # Initialize cache if enabled
        if settings.ENABLE_EMBEDDING_CACHE:
            self.cache = TTLCache(
                maxsize=settings.EMBEDDING_CACHE_MAX_SIZE,
                ttl=settings.EMBEDDING_CACHE_TTL
            )
            logger.info(f"✅ Embedding cache initialized (max_size={settings.EMBEDDING_CACHE_MAX_SIZE}, ttl={settings.EMBEDDING_CACHE_TTL}s)")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"cohere:{self.model_name}:{text_hash}"
    
    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache if available"""
        if not self.cache:
            return None
        
        cache_key = self._get_cache_key(text)
        entry = self.cache.get(cache_key)
        
        if entry and isinstance(entry, EmbeddingCacheEntry):
            if datetime.utcnow() < entry.expires_at:
                self.cache_stats["hits"] += 1
                return entry.embedding
            else:
                # Expired entry
                del self.cache[cache_key]
        
        self.cache_stats["misses"] += 1
        return None
    
    def _save_to_cache(self, text: str, embedding: List[float]):
        """Save embedding to cache"""
        if not self.cache:
            return
        
        cache_key = self._get_cache_key(text)
        entry = EmbeddingCacheEntry(embedding, self.model_name)
        self.cache[cache_key] = entry
    
    async def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call_time
        
        if time_since_last_call < self.min_time_between_calls:
            wait_time = self.min_time_between_calls - time_since_last_call
            logger.debug(f"⏳ Rate limiting: waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        self.last_api_call_time = time.time()
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode image file to base64 string"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        self.cache_stats["total_requests"] += 1
        self.cache_stats["text_requests"] += 1
        
        # Check cache first
        cached_embedding = self._get_from_cache(text)
        if cached_embedding:
            logger.debug(f"✅ Cache hit for text (length={len(text)})")
            return cached_embedding
        
        # Check if API key is set
        if not self.cohere_api_key:
            logger.error("❌ Cohere API key not configured")
            raise ValueError("Cohere API key not configured")
        
        # Rate limiting
        await self._rate_limit()
        
        try:
            # Call Cohere API via HTTP
            self.cache_stats["api_calls"] += 1
            logger.debug(f"🔄 Calling Cohere API for text (length={len(text)})")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.cohere_base_url}/embed",
                    headers={
                        "Authorization": f"Bearer {self.cohere_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "texts": [text],
                        "model": self.text_model_name,
                        "input_type": "search_document"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                if "embeddings" not in data or not data["embeddings"]:
                    raise ValueError("No embeddings returned from Cohere API")
                
                embedding = data["embeddings"][0]
            
            # Validate embedding
            if not embedding or len(embedding) != self.embedding_dimensions:
                raise ValueError(f"Invalid embedding dimensions: expected {self.embedding_dimensions}, got {len(embedding) if embedding else 0}")
            
            # Cache the result
            self._save_to_cache(text, embedding)
            
            logger.debug(f"✅ Generated text embedding (dimensions={len(embedding)})")
            return embedding
            
        except httpx.HTTPStatusError as e:
            self.cache_stats["errors"] += 1
            logger.error(f"❌ Cohere API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"❌ Error generating text embedding: {e}")
            raise
    
    async def embed_image(self, image_path: str, image_description: Optional[str] = None) -> List[float]:
        """
        Generate embedding for an image
        
        Args:
            image_path: Path to image file
            image_description: Optional text description to combine with image
            
        Returns:
            List of floats representing the embedding vector
        """
        self.cache_stats["total_requests"] += 1
        self.cache_stats["image_requests"] += 1
        
        # Check if API key is set
        if not self.cohere_api_key:
            logger.error("❌ Cohere API key not configured")
            raise ValueError("Cohere API key not configured")
        
        # Check if file exists
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        # Rate limiting
        await self._rate_limit()
        
        try:
            # Encode image to base64
            image_base64 = self._encode_image_to_base64(image_path)
            
            # Call Cohere API via HTTP
            self.cache_stats["api_calls"] += 1
            logger.debug(f"🔄 Calling Cohere API for image: {image_path}")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.cohere_base_url}/embed",
                    headers={
                        "Authorization": f"Bearer {self.cohere_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "images": [image_base64],
                        "model": self.multimodal_model_name,
                        "input_type": "image"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                if "embeddings" not in data or not data["embeddings"]:
                    raise ValueError("No embeddings returned from Cohere API")
                
                embedding = data["embeddings"][0]
            
            # Validate embedding
            if not embedding or len(embedding) != self.embedding_dimensions:
                raise ValueError(f"Invalid embedding dimensions: expected {self.embedding_dimensions}, got {len(embedding) if embedding else 0}")
            
            logger.debug(f"✅ Generated image embedding (dimensions={len(embedding)})")
            return embedding
            
        except httpx.HTTPStatusError as e:
            self.cache_stats["errors"] += 1
            logger.error(f"❌ Cohere API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"❌ Error generating image embedding: {e}")
            raise
    
    async def embed_multimodal(self, text: Optional[str] = None, image_path: Optional[str] = None) -> List[float]:
        """
        Generate embedding for combined text and image
        
        Args:
            text: Optional text content
            image_path: Optional path to image file
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text and not image_path:
            raise ValueError("Must provide either text or image_path")
        
        if text and not image_path:
            return await self.embed_text(text)
        
        if image_path and not text:
            return await self.embed_image(image_path)
        
        # Both text and image provided - combine them
        self.cache_stats["total_requests"] += 1
        
        # Check if API key is set
        if not self.cohere_api_key:
            logger.error("❌ Cohere API key not configured")
            raise ValueError("Cohere API key not configured")
        
        # Rate limiting
        await self._rate_limit()
        
        try:
            # Encode image to base64
            image_base64 = self._encode_image_to_base64(image_path)
            
            # Call Cohere API with both text and image via HTTP
            self.cache_stats["api_calls"] += 1
            logger.debug(f"🔄 Calling Cohere API for multimodal (text + image)")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.cohere_base_url}/embed",
                    headers={
                        "Authorization": f"Bearer {self.cohere_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "texts": [text],
                        "images": [image_base64],
                        "model": self.multimodal_model_name,
                        "input_type": "search_document"
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                if "embeddings" not in data or not data["embeddings"]:
                    raise ValueError("No embeddings returned from Cohere API")
                
                embedding = data["embeddings"][0]
            
            # Validate embedding
            if not embedding or len(embedding) != self.embedding_dimensions:
                raise ValueError(f"Invalid embedding dimensions: expected {self.embedding_dimensions}, got {len(embedding) if embedding else 0}")
            
            logger.debug(f"✅ Generated multimodal embedding (dimensions={len(embedding)})")
            return embedding
            
        except httpx.HTTPStatusError as e:
            self.cache_stats["errors"] += 1
            logger.error(f"❌ Cohere API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"❌ Error generating multimodal embedding: {e}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        
        return embeddings
    
    # Compatibility methods for existing code
    async def generate_embedding(self, text: str) -> List[float]:
        """Alias for embed_text for backward compatibility"""
        return await self.embed_text(text)
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Alias for embed_texts for backward compatibility"""
        return await self.embed_texts(texts)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = self.cache_stats.copy()
        
        if self.cache:
            stats["cache_size"] = len(self.cache)
            stats["cache_max_size"] = self.cache.maxsize
        
        if stats["total_requests"] > 0:
            stats["cache_hit_rate"] = stats["hits"] / stats["total_requests"]
        else:
            stats["cache_hit_rate"] = 0.0
        
        return stats
    
    def clear_cache(self):
        """Clear the embedding cache"""
        if self.cache:
            self.cache.clear()
            logger.info("🗑️  Embedding cache cleared")


# Global instance
_cohere_service = None


def get_cohere_embeddings_service() -> CohereEmbeddingsService:
    """Get or create the global Cohere embeddings service instance"""
    global _cohere_service
    if _cohere_service is None:
        _cohere_service = CohereEmbeddingsService()
    return _cohere_service
