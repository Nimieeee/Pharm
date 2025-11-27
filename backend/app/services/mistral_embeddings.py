"""
Mistral Embeddings Service
Handles embedding generation using Mistral API via direct HTTP calls with caching
"""

import asyncio
import hashlib
import httpx
import json
import logging
import time
import threading
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from cachetools import TTLCache

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
    """Service for generating embeddings using Mistral API via direct HTTP calls"""
    
    def __init__(self):
        self.mistral_api_key = settings.MISTRAL_API_KEY
        self.mistral_base_url = "https://api.mistral.ai/v1"
        self.model_name = "mistral-embed"
        self.embedding_dimensions = 1024  # mistral-embed dimensions
        self.cache = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "api_calls": 0,
            "total_requests": 0
        }
        # Rate limiting: Mistral free tier - conservative approach
        self.last_api_call_time = 0
        self.min_time_between_calls = 1.5  # 1.5 seconds to be safe
        self.max_batch_size = 16  # Mistral supports up to 16 texts per request
        self.rate_limit_lock = threading.Lock()  # Thread-safe rate limiting
        
        # Check API key
        if self.mistral_api_key:
            logger.info(f"✅ Mistral embeddings API initialized: {self.model_name}")
        else:
            logger.warning("⚠️  Mistral API key not configured")
        
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
        return f"{self.model_name}:{text_hash}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        if not self.cache:
            return None
        
        try:
            entry = self.cache.get(cache_key)
            if entry and isinstance(entry, EmbeddingCacheEntry):
                if datetime.utcnow() < entry.expires_at:
                    self.cache_stats["hits"] += 1
                    return entry.embedding
                else:
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
            entry = EmbeddingCacheEntry(embedding, self.model_name)
            self.cache[cache_key] = entry
        except Exception as e:
            logger.error(f"❌ Cache storage error: {e}")
            self.cache_stats["errors"] += 1
    
    async def _generate_embedding_with_api(self, text: str) -> Optional[List[float]]:
        """Generate embedding using Mistral API with retry logic and rate limiting"""
        if not self.mistral_api_key:
            return None
        
        max_retries = 5
        base_delay = 1.0  # Base delay for exponential backoff
        
        for attempt in range(max_retries):
            try:
                # Thread-safe rate limiting
                with self.rate_limit_lock:
                    current_time = time.time()
                    time_since_last_call = current_time - self.last_api_call_time
                    if time_since_last_call < self.min_time_between_calls:
                        wait_time = self.min_time_between_calls - time_since_last_call
                        logger.debug(f"⏱️  Rate limiting: waiting {wait_time:.2f}s")
                        await asyncio.sleep(wait_time)
                    
                    # Update last call time immediately after waiting
                    self.last_api_call_time = time.time()
                
                self.cache_stats["api_calls"] += 1
                start_time = time.time()
                
                # Prepare request payload
                payload = {
                    "model": self.model_name,
                    "input": [text]
                }
                
                # Make HTTP request to Mistral API
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.mistral_base_url}/embeddings",
                        headers={
                            "Authorization": f"Bearer {self.mistral_api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        duration = time.time() - start_time
                        logger.debug(f"✅ Mistral embedding generated in {duration:.2f}s")
                        
                        # Extract embedding from response
                        if result.get("data") and len(result["data"]) > 0:
                            embedding = result["data"][0]["embedding"]
                            return embedding
                        else:
                            logger.error("❌ No embedding data in Mistral API response")
                            return None
                    
                    elif response.status_code == 429:
                        # Rate limit exceeded - exponential backoff
                        if attempt < max_retries - 1:
                            retry_delay = base_delay * (2 ** attempt)
                            logger.warning(f"⚠️  Rate limit hit (429), retrying in {retry_delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"❌ Rate limit exceeded after {max_retries} attempts")
                            return None
                    
                    elif response.status_code >= 500:
                        # Server error - retry with backoff
                        if attempt < max_retries - 1:
                            retry_delay = base_delay * (2 ** attempt)
                            logger.warning(f"⚠️  Server error ({response.status_code}), retrying in {retry_delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"❌ Server error after {max_retries} attempts: {response.status_code}")
                            return None
                    
                    else:
                        logger.error(f"❌ Mistral API error: {response.status_code} - {response.text}")
                        return None
                
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    retry_delay = base_delay * (2 ** attempt)
                    logger.warning(f"⚠️  Request timeout, retrying in {retry_delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ Request timeout after {max_retries} attempts")
                    return None
            
            except Exception as e:
                if attempt < max_retries - 1:
                    retry_delay = base_delay * (2 ** attempt)
                    logger.warning(f"⚠️  API error: {e}, retrying in {retry_delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ Mistral API error after {max_retries} attempts: {e}")
                    return None
        
        return None
    
    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Generate fallback hash-based embedding"""
        try:
            if not text.strip():
                return [0.0] * self.embedding_dimensions
            
            hash_obj = hashlib.sha256(text.encode('utf-8'))
            hash_bytes = hash_obj.digest()
            
            embedding = []
            for i in range(self.embedding_dimensions):
                byte_val = hash_bytes[i % len(hash_bytes)]
                embedding.append((byte_val / 255.0) * 2.0 - 1.0)
            
            return embedding
        except Exception as e:
            logger.error(f"❌ Error generating fallback embedding: {e}")
            return [0.0] * self.embedding_dimensions
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text with caching and fallback"""
        if not text or not text.strip():
            logger.warning("⚠️  Empty text provided for embedding generation")
            return None
        
        self.cache_stats["total_requests"] += 1
        
        # Clean and truncate text
        clean_text = text.strip()
        if len(clean_text) > 8000:
            clean_text = clean_text[:8000]
            logger.warning(f"⚠️  Text truncated to 8000 characters for embedding")
        
        # Check cache first
        cache_key = self._generate_cache_key(clean_text)
        cached_embedding = self._get_from_cache(cache_key)
        if cached_embedding:
            logger.debug("✅ Embedding retrieved from cache")
            return cached_embedding
        
        # Try Mistral API
        if self.mistral_api_key:
            embedding = await self._generate_embedding_with_api(clean_text)
            if embedding:
                self._store_in_cache(cache_key, embedding)
                logger.debug("✅ Embedding generated via Mistral API")
                return embedding
        
        # Fallback to hash-based embedding
        if settings.FALLBACK_TO_HASH_EMBEDDINGS:
            embedding = self._generate_fallback_embedding(clean_text)
            if self.cache:
                try:
                    entry = EmbeddingCacheEntry(embedding, "hash-fallback")
                    entry.expires_at = datetime.utcnow() + timedelta(seconds=300)
                    self.cache[cache_key] = entry
                except Exception as e:
                    logger.error(f"❌ Error caching fallback embedding: {e}")
            
            logger.warning("⚠️  Using fallback hash-based embedding")
            return embedding
        
        logger.error("❌ Failed to generate embedding - no fallback enabled")
        return None
    
    async def _generate_embeddings_batch_with_api(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts using batch API (up to 16 at once)"""
        if not self.mistral_api_key or not texts:
            return [None] * len(texts)
        
        max_retries = 5
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Thread-safe rate limiting
                with self.rate_limit_lock:
                    current_time = time.time()
                    time_since_last_call = current_time - self.last_api_call_time
                    if time_since_last_call < self.min_time_between_calls:
                        wait_time = self.min_time_between_calls - time_since_last_call
                        await asyncio.sleep(wait_time)
                    
                    # Update last call time immediately after waiting
                    self.last_api_call_time = time.time()
                
                self.cache_stats["api_calls"] += 1
                start_time = time.time()
                
                # Prepare batch request
                payload = {
                    "model": self.model_name,
                    "input": texts  # Send multiple texts at once
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.mistral_base_url}/embeddings",
                        headers={
                            "Authorization": f"Bearer {self.mistral_api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload,
                        timeout=60.0  # Longer timeout for batch
                    )
                    
                    self.last_api_call_time = time.time()
                    
                    if response.status_code == 200:
                        result = response.json()
                        duration = time.time() - start_time
                        logger.debug(f"✅ Batch of {len(texts)} embeddings generated in {duration:.2f}s")
                        
                        if result.get("data") and len(result["data"]) == len(texts):
                            return [item["embedding"] for item in result["data"]]
                        else:
                            logger.error("❌ Batch embedding response length mismatch")
                            return [None] * len(texts)
                    
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            retry_delay = base_delay * (2 ** attempt)
                            logger.warning(f"⚠️  Rate limit hit, retrying in {retry_delay:.1f}s")
                            await asyncio.sleep(retry_delay)
                            continue
                        return [None] * len(texts)
                    
                    else:
                        logger.error(f"❌ Batch API error: {response.status_code}")
                        return [None] * len(texts)
            
            except Exception as e:
                if attempt < max_retries - 1:
                    retry_delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(retry_delay)
                    continue
                logger.error(f"❌ Batch embedding error: {e}")
                return [None] * len(texts)
        
        return [None] * len(texts)
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts with intelligent batching"""
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Check cache first
        embeddings = []
        uncached_indices = []
        uncached_texts = []
        
        for i, text in enumerate(texts):
            cache_key = self._generate_cache_key(text)
            cached_embedding = self._get_from_cache(cache_key)
            if cached_embedding:
                embeddings.append(cached_embedding)
            else:
                embeddings.append(None)
                uncached_indices.append(i)
                uncached_texts.append(text)
        
        if not uncached_texts:
            logger.info(f"✅ All {len(texts)} embeddings retrieved from cache")
            return embeddings
        
        logger.info(f"📡 Fetching {len(uncached_texts)} uncached embeddings (batch API)")
        
        # Process uncached texts in batches of max_batch_size
        for batch_start in range(0, len(uncached_texts), self.max_batch_size):
            batch_end = min(batch_start + self.max_batch_size, len(uncached_texts))
            batch_texts = uncached_texts[batch_start:batch_end]
            batch_indices = uncached_indices[batch_start:batch_end]
            
            # Get embeddings for this batch
            batch_embeddings = await self._generate_embeddings_batch_with_api(batch_texts)
            
            # Store in cache and results
            for i, embedding in enumerate(batch_embeddings):
                global_idx = batch_indices[i]
                if embedding:
                    cache_key = self._generate_cache_key(batch_texts[i])
                    self._store_in_cache(cache_key, embedding)
                    embeddings[global_idx] = embedding
        
        success_count = sum(1 for emb in embeddings if emb is not None)
        logger.info(f"✅ Generated {success_count}/{len(texts)} embeddings successfully")
        
        return embeddings
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache and model statistics"""
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
        
        stats["api_available"] = self.mistral_api_key is not None
        stats["model_name"] = self.model_name
        stats["dimensions"] = self.embedding_dimensions
        
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
            "api_available": self.mistral_api_key is not None,
            "cache_enabled": self.cache is not None,
            "model_name": self.model_name,
            "dimensions": self.embedding_dimensions,
            "errors": []
        }
        
        # Test embedding generation
        try:
            test_embedding = await self.generate_embedding("test")
            if test_embedding and len(test_embedding) == self.embedding_dimensions:
                health["embedding_test"] = "passed"
            else:
                health["embedding_test"] = "failed"
                health["errors"].append("Embedding generation test failed")
                health["status"] = "degraded"
        except Exception as e:
            health["embedding_test"] = "error"
            health["errors"].append(f"Embedding test error: {str(e)}")
            health["status"] = "unhealthy"
        
        health["cache_stats"] = self.get_cache_stats()
        
        return health


# Global embeddings service instance
_mistral_service = None


def get_mistral_embeddings_service() -> MistralEmbeddingsService:
    """Get or create the global Mistral embeddings service instance"""
    global _mistral_service
    if _mistral_service is None:
        _mistral_service = MistralEmbeddingsService()
    return _mistral_service


# Backward compatibility
embeddings_service = get_mistral_embeddings_service()
HuggingFaceEmbeddingsService = MistralEmbeddingsService
