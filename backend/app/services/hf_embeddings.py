"""
HuggingFace Embeddings Service
Handles embedding generation using sentence-transformers with caching
"""

import asyncio
import hashlib
import logging
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from cachetools import TTLCache

from app.core.config import settings

logger = logging.getLogger(__name__)

# Import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("⚠️  sentence-transformers not available")


class EmbeddingCacheEntry:
    """Cache entry for embeddings"""
    def __init__(self, embedding: List[float], model_version: str):
        self.embedding = embedding
        self.model_version = model_version
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=settings.EMBEDDING_CACHE_TTL)


class HuggingFaceEmbeddingsService:
    """Service for generating embeddings using HuggingFace sentence-transformers"""
    
    def __init__(self):
        self.model = None
        self.model_name = getattr(settings, 'HUGGINGFACE_MODEL', 'all-MiniLM-L6-v2')
        self.embedding_dimensions = 384  # all-MiniLM-L6-v2 dimensions
        self.cache = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "model_calls": 0,
            "total_requests": 0
        }
        
        # Initialize model if available
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Loading HuggingFace model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info(f"✅ HuggingFace embeddings model loaded: {self.model_name}")
            except Exception as e:
                logger.error(f"❌ Failed to load HuggingFace model: {e}")
                self.model = None
        else:
            logger.warning("⚠️  sentence-transformers not installed")
        
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
    
    async def _generate_embedding_with_model(self, text: str) -> Optional[List[float]]:
        """Generate embedding using the loaded model"""
        if not self.model:
            return None
        
        try:
            self.cache_stats["model_calls"] += 1
            start_time = time.time()
            
            # Run model in thread pool to avoid blocking
            embedding = await asyncio.to_thread(
                self.model.encode,
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            duration = time.time() - start_time
            logger.debug(f"HuggingFace embedding generated in {duration:.2f}s")
            
            # Convert to list
            embedding_list = embedding.tolist()
            return embedding_list
            
        except Exception as e:
            logger.error(f"❌ HuggingFace model error: {e}")
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
        
        # Try HuggingFace model
        if self.model:
            embedding = await self._generate_embedding_with_model(clean_text)
            if embedding:
                self._store_in_cache(cache_key, embedding)
                logger.debug("✅ Embedding generated via HuggingFace model")
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
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        if not texts:
            return []
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        # Process texts concurrently
        semaphore = asyncio.Semaphore(10)  # Limit concurrent operations
        
        async def process_text(text: str) -> Optional[List[float]]:
            async with semaphore:
                return await self.generate_embedding(text)
        
        tasks = [process_text(text) for text in texts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
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
        
        stats["model_available"] = self.model is not None
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
            "model_available": self.model is not None,
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
embeddings_service = HuggingFaceEmbeddingsService()
