"""
Sentence Transformer Embeddings Service
Local embeddings - no API calls, no rate limits, instant processing
Uses all-MiniLM-L6-v2 model (384 dimensions)
"""

import logging
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from cachetools import TTLCache
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingCacheEntry:
    """Cache entry for embeddings"""
    def __init__(self, embedding: List[float], model_version: str):
        self.embedding = embedding
        self.model_version = model_version
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=settings.EMBEDDING_CACHE_TTL)


class SentenceTransformerEmbeddingsService:
    """Service for generating embeddings using local Sentence Transformers"""
    

    def __init__(self):
        self.model_name = "nomic-ai/nomic-embed-text-v1.5"
        self.embedding_dimensions = 768  # Nomic default
        self.model = None
        self.cache = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0,
            "total_requests": 0,
            "model_calls": 0
        }
        
        # Initialize cache if enabled
        if settings.ENABLE_EMBEDDING_CACHE:
            self.cache = TTLCache(
                maxsize=settings.EMBEDDING_CACHE_MAX_SIZE,
                ttl=settings.EMBEDDING_CACHE_TTL
            )
            logger.info(f"✅ Embedding cache initialized (max_size={settings.EMBEDDING_CACHE_MAX_SIZE}, ttl={settings.EMBEDDING_CACHE_TTL}s)")
        
        # Load model lazily on first use
        logger.info(f"📦 Nomic Embed service initialized (model will load on first use)")
    
    def _load_model(self):
        """Load the sentence transformer model"""
        if self.model is None:
            logger.info(f"🔄 Loading Nomic model: {self.model_name}")
            try:
                self.model = SentenceTransformer(self.model_name, trust_remote_code=True)
                logger.info(f"✅ Model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load model: {e}")
                raise
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"st:{self.model_name}:{text_hash}"
    
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
    
    async def generate_embedding(self, text: str) -> List[float]:
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
        
        # Load model if not loaded
        self._load_model()
        
        try:
            # Generate embedding locally (no API call!)
            self.cache_stats["model_calls"] += 1
            logger.debug(f"🔄 Generating local embedding for text (length={len(text)})")
            
            # Add prefix for Nomic (search_query: for queries)
            input_text = f"search_query: {text}"
            
            # Encode returns numpy array, convert to list
            embedding = self.model.encode(input_text, convert_to_tensor=False).tolist()
            
            # Validate embedding
            if not embedding or len(embedding) != self.embedding_dimensions:
                raise ValueError(f"Invalid embedding dimensions: expected {self.embedding_dimensions}, got {len(embedding) if embedding else 0}")
            
            # Cache the result
            self._save_to_cache(text, embedding)
            
            logger.debug(f"✅ Generated local embedding (dimensions={len(embedding)})")
            return embedding
            
        except Exception as e:
            self.cache_stats["errors"] += 1
            logger.error(f"❌ Error generating embedding: {e}")
            raise
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts (batch processing for speed)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Load model if not loaded
        self._load_model()
        
        # Check cache for all texts
        embeddings = []
        texts_to_process = []
        text_indices = []
        
        for i, text in enumerate(texts):
            cached = self._get_from_cache(text)
            if cached:
                embeddings.append(cached)
            else:
                embeddings.append(None)  # Placeholder
                # Add prefix for Nomic (search_document: for documents)
                texts_to_process.append(f"search_document: {text}")
                text_indices.append(i)
        
        # Process uncached texts in batch
        if texts_to_process:
            try:
                logger.info(f"🔄 Batch processing {len(texts_to_process)} embeddings")
                self.cache_stats["model_calls"] += 1
                
                # Batch encode is much faster than individual encodes
                batch_embeddings = self.model.encode(texts_to_process, convert_to_tensor=False, show_progress_bar=False)
                
                # Store results and cache
                for idx, embedding in zip(text_indices, batch_embeddings):
                    embedding_list = embedding.tolist()
                    embeddings[idx] = embedding_list
                    self._save_to_cache(texts[idx], embedding_list)
                
                logger.info(f"✅ Batch processed {len(texts_to_process)} embeddings")
                
            except Exception as e:
                self.cache_stats["errors"] += 1
                logger.error(f"❌ Error in batch processing: {e}")
                # Fill failed embeddings with None
                for idx in text_indices:
                    if embeddings[idx] is None:
                        embeddings[idx] = None
        
        self.cache_stats["total_requests"] += len(texts)
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
_sentence_transformer_service = None


def get_sentence_transformer_service() -> SentenceTransformerEmbeddingsService:
    """Get or create the global Sentence Transformer service instance"""
    global _sentence_transformer_service
    if _sentence_transformer_service is None:
        _sentence_transformer_service = SentenceTransformerEmbeddingsService()
    return _sentence_transformer_service
