"""
Mistral Embeddings Service
Handles embedding generation using Mistral API with caching and error handling
"""

import asyncio
import hashlib
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from cachetools import TTLCache
from mistralai.client import MistralClient
from mistralai.models.embeddings import EmbeddingRequest

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingCacheEntry:
    """Cache entry for embeddings"""
    def __init__(self, embedding: List[float], model_version: str):
        self.embedding = embedding
        self.model_version = model_version
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=settings.EMBEDDING_CACHE_TTL)


class MistralEmbeddingsService:
    """Service for generating embeddings using Mistral API"""
    
    def __init__(self):
        self.client = None
        self.cache = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "api_calls": 0,
            "total_requests": 0
        }
        
        # Initialize client if API key is available
        if settings.MISTRAL_API_KEY:
            try:
                self.client = MistralClient(api_key=settings.MISTRAL_API_KEY)
                logger.info("✅ Mistral embeddings client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Mistral client: {e}")
                self.client = None
        else:
            logger.warning("⚠️  Mistral API key not provided - using fallback embeddings")
        
        # Initialize cache if enabled
        if settings.ENABLE_EMBEDDING_CACHE:
            self.cache = TTLCache(
                maxsize=settings.EMBEDDING_CACHE_MAX_SIZE,
                ttl=settings.EMBEDDING_CACHE_TTL
            )
            logger.info(f"✅ Embedding cache initialized (max_size={settings.EMBEDDING_CACHE_MAX_SIZE}, ttl={settings.EMBEDDING_CACHE_TTL}s)")
    
    def _generate_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        return f"{settings.MISTRAL_EMBED_MODEL}:{text_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        if not self.cache:
            return None
        
        try:
            entry = self.cache.get(cache_key)
            if entry and isinstance(entry, EmbeddingCacheEntry):
                # Check if entry is still valid
                if datetime.utcnow() < entry.expires_at:
                    self.cache_stats["hits"] += 1
                    return entry.embedding
                else:
                    # Remove expired entry
                    del self.cache[cache_key]
            
            self.cache_stats["misses"] += 1
            return None
        except Exception as e:
            logger.error(f"❌ Cache retrieval error: {e}")
            self.cache_stats["errors"] += 1
            return None
    
    def _store_in_cache(self, cache_key: str, embedding: List[float]) -> None:
        """Store embedding in cache"""
        if not self.cache:
            return
        
        try:
            entry = EmbeddingCacheEntry(embedding, settings.MISTRAL_EMBED_MODEL)
            self.cache[cache_key] = entry
        except Exception as e:
            logger.error(f"❌ Cache storage error: {e}")
            self.cache_stats["errors"] += 1
    
    async def _call_mistral_api(self, text: str, retry_count: int = 0) -> Optional[List[float]]:
        """Call Mistral API with retry logic"""
        if not self.client:
            return None
        
        try:
            self.cache_stats["api_calls"] += 1
            
            # Create embedding request
            request = EmbeddingRequest(
                model=settings.MISTRAL_EMBED_MODEL,
                input=[text]
            )
            
            # Make API call with timeout
            start_time = time.time()
            response = await asyncio.wait_for(
                asyncio.to_thread(self.client.embeddings, request),
                timeout=settings.MISTRAL_TIMEOUT
            )
            
            api_time = time.time() - start_time
            logger.debug(f"Mistral API call completed in {api_time:.2f}s")
            
            # Extract embedding from response
            if response and response.data and len(response.data) > 0:
                embedding = response.data[0].embedding
                if len(embedding) == settings.MISTRAL_EMBED_DIMENSIONS:
                    return embedding
                else:
                    logger.error(f"❌ Unexpected embedding dimensions: {len(embedding)} (expected {settings.MISTRAL_EMBED_DIMENSIONS})")
                    return None
            else:
                logger.error("❌ Empty or invalid response from Mistral API")
                return None
                
        except asyncio.TimeoutError:
            logger.error(f"❌ Mistral API timeout after {settings.MISTRAL_TIMEOUT}s")
            return await self._handle_retry(text, retry_count, "timeout")
            
        except Exception as e:
            logger.error(f"❌ Mistral API error: {e}")
            return await self._handle_retry(text, retry_count, str(e))
    
    async def _handle_retry(self, text: str, retry_count: int, error_reason: str) -> Optional[List[float]]:
        """Handle API retry with exponential backoff"""
        if retry_count >= settings.MISTRAL_MAX_RETRIES:
            logger.error(f"❌ Max retries ({settings.MISTRAL_MAX_RETRIES}) exceeded for embedding generation")
            return None
        
        # Exponential backoff with jitter
        delay = (2 ** retry_count) + (0.1 * retry_count)  # 1, 2.1, 4.2, etc.
        logger.warning(f"⚠️  Retrying Mistral API call in {delay:.1f}s (attempt {retry_count + 1}/{settings.MISTRAL_MAX_RETRIES})")
        
        await asyncio.sleep(delay)
        return await self._call_mistral_api(text, retry_count + 1)
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate fallback hash-based embedding"""
        try:
            if not text.strip():
                return [0.0] * settings.MISTRAL_EMBED_DIMENSIONS
            
            # Generate hash-based embedding
            hash_obj = hashlib.sha256(text.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            
            # Convert to embedding dimensions
            embedding = []
            for i in range(settings.MISTRAL_EMBED_DIMENSIONS):
                byte_val = hash_bytes[i % len(hash_bytes)]
                # Normalize to [-1, 1] range
                embedding.append((byte_val / 255.0) * 2.0 - 1.0)
            
            return embedding
        except Exception as e:
            logger.error(f"❌ Error generating fallback embedding: {e}")
            return [0.0] * settings.MISTRAL_EMBED_DIMENSIONS
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text with caching and fallback"""
        if not text or not text.strip():
            logger.warning("⚠️  Empty text provided for embedding generation")
            return None
        
        self.cache_stats["total_requests"] += 1
        
        # Clean and truncate text
        clean_text = text.strip()
        if len(clean_text) > 8000:  # Mistral API limit
            clean_text = clean_text[:8000]
            logger.warning(f"⚠️  Text truncated to 8000 characters for embedding")
        
        # Check cache first
        cache_key = self._generate_cache_key(clean_text)
        cached_embedding = self._get_from_cache(cache_key)
        if cached_embedding:
            logger.debug("✅ Embedding retrieved from cache")
            return cached_embedding
        
        # Try Mistral API if enabled and available
        if settings.USE_MISTRAL_EMBEDDINGS and self.client:
            embedding = await self._call_mistral_api(clean_text)
            if embedding:
                # Store in cache
                self._store_in_cache(cache_key, embedding)
                logger.debug("✅ Embedding generated via Mistral API")
                return embedding
        
        # Fallback to hash-based embedding
        if settings.FALLBACK_TO_HASH_EMBEDDINGS:
            embedding = self._generate_fallback_embedding(clean_text)
            # Store fallback in cache with shorter TTL
            if self.cache:
                try:
                    entry = EmbeddingCacheEntry(embedding, "hash-fallback")
                    entry.expires_at = datetime.utcnow() + timedelta(seconds=300)  # 5 minutes
                    self.cache[cache_key] = entry
                except Exception as e:
                    logger.error(f"❌ Error caching fallback embedding: {e}")
            
            logger.warning("⚠️  Using fallback hash-based embedding")
            return embedding
        
        logger.error("❌ Failed to generate embedding - no fallback enabled")
        return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Process texts concurrently with semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
        
        async def process_text(text: str) -> Optional[List[float]]:
            async with semaphore:
                return await self.generate_embedding(text)
        
        tasks = [process_text(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        embeddings = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Error generating embedding for text {i}: {result}")
                embeddings.append(None)
            else:
                embeddings.append(result)
        
        success_count = sum(1 for emb in embeddings if emb is not None)
        logger.info(f"✅ Generated {success_count}/{len(texts)} embeddings successfully")
        
        return embeddings
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache and API statistics"""
        stats = self.cache_stats.copy()
        
        if stats["total_requests"] > 0:
            stats["cache_hit_rate"] = stats["hits"] / stats["total_requests"]
        else:
            stats["cache_hit_rate"] = 0.0
        
        if self.cache:
            stats["cache_size"] = len(self.cache)
            stats["cache_max_size"] = self.cache.maxsize
        else:
            stats["cache_size"] = 0
            stats["cache_max_size"] = 0
        
        stats["client_available"] = self.client is not None
        stats["model"] = settings.MISTRAL_EMBED_MODEL
        stats["dimensions"] = settings.MISTRAL_EMBED_DIMENSIONS
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear the embedding cache"""
        if self.cache:
            self.cache.clear()
            logger.info("✅ Embedding cache cleared")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the embedding service"""
        health = {
            "status": "healthy",
            "client_available": self.client is not None,
            "cache_enabled": self.cache is not None,
            "model": settings.MISTRAL_EMBED_MODEL,
            "dimensions": settings.MISTRAL_EMBED_DIMENSIONS,
            "errors": []
        }
        
        # Test embedding generation
        try:
            test_embedding = await self.generate_embedding("test")
            if test_embedding and len(test_embedding) == settings.MISTRAL_EMBED_DIMENSIONS:
                health["embedding_test"] = "passed"
            else:
                health["embedding_test"] = "failed"
                health["errors"].append("Embedding generation test failed")
                health["status"] = "degraded"
        except Exception as e:
            health["embedding_test"] = "error"
            health["errors"].append(f"Embedding test error: {str(e)}")
            health["status"] = "unhealthy"
        
        # Add cache stats
        health["cache_stats"] = self.get_cache_stats()
        
        return health


# Global embeddings service instance
embeddings_service = MistralEmbeddingsService()