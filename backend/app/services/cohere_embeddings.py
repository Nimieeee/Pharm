"""
Cohere Embeddings Service
Handles embedding generation using Cohere API with caching
Much faster than Mistral - 100 requests/minute on free tier
"""

import asyncio
import hashlib
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from cachetools import TTLCache
import cohere

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
        self.model_name = "embed-english-v3.0"
        self.embedding_dimensions = 1024  # Cohere embed-english-v3.0 dimensions
        self.cache = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "api_calls": 0,
            "total_requests": 0
        }
        # Rate limiting: Cohere free tier allows 100 requests per minute
        self.last_api_call_time = 0
        self.min_time_between_calls = 0.6  # 0.6 seconds = 100 requests/minute
        
        # Initialize Cohere client
        if not self.cohere_api_key:
            logger.warning("⚠️  COHERE_API_KEY not set - embeddings will fail")
            self.client = None
        else:
            try:
                self.client = cohere.Client(self.cohere_api_key)
                logger.info("✅ Cohere client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Cohere client: {e}")
                self.client = None
        
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
    
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        self.cache_stats["total_requests"] += 1
        
        # Check cache first
        cached_embedding = self._get_from_cache(text)
        if cached_embedding:
            logger.debug(f"✅ Cache hit for text (length={len(text)})")
            return cached_embedding
        
        # Check if client is initialized
        if not self.client:
            logger.error("❌ Cohere client not initialized")
            raise ValueError("Cohere API key not configured")
        
        # Rate limiting
        await self._rate_limit()
        
        try:
            # Call Cohere API
            self.cache_stats["api_calls"] += 1
            logger.debug(f"🔄 Calling Cohere API for text (length={len(text)})")
            
            response = self.client.embed(
                texts=[text],
                model=self.model_name,
                input_type="search_document"  # For document indexing
            )
            
            embedding = response.embeddings[0]
            
            # Validate embedding
            if not embedding or len(embedding) != self.embedding_dimensions:
                raise ValueError(f"Invalid embedding dimensions: expected {self.embedding_dimensions}, got {len(embedding) if embedding else 0}")
            
            # Cache the result
            self._save_to_cache(text, embedding)
            
            logger.debug(f"✅ Generated embedding (dimensions={len(embedding)})")
            return embedding
            
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"❌ Error generating embedding: {e}")
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
