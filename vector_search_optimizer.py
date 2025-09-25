"""
Vector Search Optimizer with improved indexing and performance
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from supabase import Client
import numpy as np
from datetime import datetime, timedelta

from vector_retriever import Document, VectorRetriever
from performance_optimizer import performance_optimizer

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Enhanced search result with performance metrics"""
    documents: List[Document]
    search_time_ms: float
    total_documents_searched: int
    cache_hit: bool = False
    index_used: Optional[str] = None

@dataclass
class IndexStats:
    """Vector index statistics"""
    index_name: str
    total_vectors: int
    index_size_mb: float
    last_updated: datetime
    avg_search_time_ms: float

class VectorSearchOptimizer:
    """Optimized vector search with caching and performance improvements"""
    
    def __init__(self, supabase_client: Optional[Client] = None, embedding_model=None):
        """Initialize vector search optimizer"""
        self.supabase_client = supabase_client or self._get_supabase_client()
        self.embedding_model = embedding_model
        self.cache_ttl = 600  # 10 minutes cache TTL for search results
        
        # Search configuration
        self.search_config = {
            "default_k": 5,
            "max_k": 20,
            "similarity_threshold": 0.1,
            "max_content_length": 2000,  # Truncate long content for memory efficiency
            "enable_reranking": True,
            "cache_embeddings": True
        }
    
    def _get_supabase_client(self) -> Client:
        """Initialize Supabase client"""
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")
        if not url or not key:
            # Return None for testing or when credentials are not available
            return None
        return create_client(url, key)
    
    def optimized_similarity_search(
        self, 
        query: str, 
        user_id: str,
        k: int = 5, 
        similarity_threshold: float = 0.1,
        use_cache: bool = True
    ) -> SearchResult:
        """
        Perform optimized similarity search with caching and performance tracking
        
        Args:
            query: Search query text
            user_id: User ID for filtering documents
            k: Number of documents to retrieve
            similarity_threshold: Minimum similarity threshold
            use_cache: Whether to use caching
            
        Returns:
            SearchResult with documents and performance metrics
        """
        start_time = datetime.now()
        
        # Limit k to prevent excessive memory usage
        k = min(k, self.search_config["max_k"])
        
        # Generate cache key
        cache_key = self._generate_search_cache_key(query, user_id, k, similarity_threshold)
        
        # Try cache first if enabled
        if use_cache:
            cached_result = performance_optimizer.get_cached_user_data(user_id, f"search_{cache_key}")
            if cached_result:
                logger.debug(f"Cache hit for vector search: {cache_key}")
                cached_result.cache_hit = True
                return cached_result
        
        try:
            # Get or generate query embedding
            query_embedding = self._get_cached_embedding(query, user_id)
            
            # Perform optimized vector search
            documents = self._perform_optimized_search(
                query_embedding=query_embedding,
                user_id=user_id,
                k=k,
                similarity_threshold=similarity_threshold
            )
            
            # Calculate search time
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Get total document count for user
            total_docs = self._get_user_document_count_cached(user_id)
            
            # Create search result
            search_result = SearchResult(
                documents=documents,
                search_time_ms=search_time,
                total_documents_searched=total_docs,
                cache_hit=False,
                index_used="ivfflat_cosine"
            )
            
            # Cache the result if enabled
            if use_cache:
                performance_optimizer.set_cached_user_data(
                    user_id, 
                    f"search_{cache_key}", 
                    search_result, 
                    ttl=self.cache_ttl
                )
            
            logger.info(f"Vector search completed in {search_time:.1f}ms, found {len(documents)} documents")
            return search_result
            
        except Exception as e:
            logger.error(f"Error in optimized similarity search: {e}")
            return SearchResult(
                documents=[],
                search_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                total_documents_searched=0,
                cache_hit=False,
                index_used=None
            )
    
    def _get_cached_embedding(self, query: str, user_id: str) -> List[float]:
        """Get or generate cached query embedding"""
        if not self.search_config["cache_embeddings"]:
            return self._generate_embedding(query)
        
        # Generate cache key for embedding
        embedding_cache_key = f"embedding_{hash(query)}"
        
        # Try cache first
        cached_embedding = performance_optimizer.get_cached_user_data(user_id, embedding_cache_key)
        if cached_embedding:
            return cached_embedding
        
        # Generate new embedding
        embedding = self._generate_embedding(query)
        
        # Cache with longer TTL since embeddings don't change
        performance_optimizer.set_cached_user_data(
            user_id, 
            embedding_cache_key, 
            embedding, 
            ttl=3600  # 1 hour TTL for embeddings
        )
        
        return embedding
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.embedding_model:
            from embeddings import get_embeddings
            self.embedding_model = get_embeddings()
        
        return self.embedding_model.embed_query(text)
    
    def _perform_optimized_search(
        self,
        query_embedding: List[float],
        user_id: str,
        k: int,
        similarity_threshold: float
    ) -> List[Document]:
        """Perform optimized vector search using database function"""
        try:
            # Use optimized database function with proper indexing
            result = self.supabase_client.rpc(
                'match_documents_optimized',
                {
                    'user_id': user_id,
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': k
                }
            ).execute()
            
            documents = []
            for row in result.data or []:
                # Truncate content for memory efficiency
                content = row['content']
                if len(content) > self.search_config["max_content_length"]:
                    content = content[:self.search_config["max_content_length"]] + "..."
                
                doc = Document(
                    id=row['id'],
                    content=content,
                    source=row['source'],
                    metadata=row.get('metadata', {}),
                    similarity=row.get('similarity', 0.0)
                )
                documents.append(doc)
            
            # Apply reranking if enabled
            if self.search_config["enable_reranking"] and len(documents) > 1:
                documents = self._rerank_documents(documents, query_embedding)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error in optimized search: {e}")
            # Fallback to basic search
            return self._fallback_search(query_embedding, user_id, k, similarity_threshold)
    
    def _fallback_search(
        self,
        query_embedding: List[float],
        user_id: str,
        k: int,
        similarity_threshold: float
    ) -> List[Document]:
        """Fallback search method if optimized search fails"""
        try:
            # Use basic match_documents function
            result = self.supabase_client.rpc(
                'match_documents',
                {
                    'user_id': user_id,
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': k
                }
            ).execute()
            
            documents = []
            for row in result.data or []:
                content = row['content']
                if len(content) > self.search_config["max_content_length"]:
                    content = content[:self.search_config["max_content_length"]] + "..."
                
                doc = Document(
                    id=row['id'],
                    content=content,
                    source=row['source'],
                    metadata=row.get('metadata', {}),
                    similarity=row.get('similarity', 0.0)
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Fallback search also failed: {e}")
            return []
    
    def _rerank_documents(self, documents: List[Document], query_embedding: List[float]) -> List[Document]:
        """Rerank documents using additional similarity metrics"""
        try:
            # Simple reranking based on content length and similarity
            def rerank_score(doc: Document) -> float:
                base_similarity = doc.similarity or 0.0
                
                # Prefer documents with moderate length (not too short, not too long)
                content_length = len(doc.content)
                length_penalty = 0.0
                if content_length < 100:
                    length_penalty = -0.1
                elif content_length > 1500:
                    length_penalty = -0.05
                
                # Boost recent documents slightly
                created_at = doc.metadata.get('created_at')
                recency_boost = 0.0
                if created_at:
                    try:
                        doc_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        days_old = (datetime.now() - doc_date).days
                        if days_old < 30:
                            recency_boost = 0.02
                    except:
                        pass
                
                return base_similarity + length_penalty + recency_boost
            
            # Sort by rerank score
            documents.sort(key=rerank_score, reverse=True)
            return documents
            
        except Exception as e:
            logger.warning(f"Reranking failed, returning original order: {e}")
            return documents
    
    def _get_user_document_count_cached(self, user_id: str) -> int:
        """Get user document count with caching"""
        cache_key = f"doc_count:{user_id}"
        
        # Try cache first
        cached_count = performance_optimizer.get_cached_user_data(user_id, "document_count")
        if cached_count is not None:
            return cached_count
        
        try:
            # Get count from database
            result = self.supabase_client.rpc(
                'get_user_document_count',
                {'user_id': user_id}
            ).execute()
            
            count = result.data or 0
            
            # Cache with medium TTL
            performance_optimizer.set_cached_user_data(user_id, "document_count", count, ttl=300)
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
    
    def _generate_search_cache_key(self, query: str, user_id: str, k: int, threshold: float) -> str:
        """Generate cache key for search results"""
        import hashlib
        key_data = f"{query}:{user_id}:{k}:{threshold}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def get_index_statistics(self) -> List[IndexStats]:
        """Get vector index statistics"""
        try:
            # Get index information from database
            result = self.supabase_client.rpc('get_vector_index_stats').execute()
            
            stats = []
            for row in result.data or []:
                stat = IndexStats(
                    index_name=row['index_name'],
                    total_vectors=row['total_vectors'],
                    index_size_mb=row['index_size_mb'],
                    last_updated=datetime.fromisoformat(row['last_updated']),
                    avg_search_time_ms=row['avg_search_time_ms']
                )
                stats.append(stat)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting index statistics: {e}")
            return []
    
    def optimize_indexes(self) -> Dict[str, Any]:
        """Optimize vector indexes for better performance"""
        try:
            # Run index optimization
            result = self.supabase_client.rpc('optimize_vector_indexes').execute()
            
            return {
                "success": True,
                "message": "Vector indexes optimized successfully",
                "details": result.data
            }
            
        except Exception as e:
            logger.error(f"Error optimizing indexes: {e}")
            return {
                "success": False,
                "message": f"Index optimization failed: {str(e)}",
                "details": None
            }
    
    def clear_search_cache(self, user_id: Optional[str] = None) -> None:
        """Clear search cache for user or all users"""
        if user_id:
            # Clear cache for specific user
            performance_optimizer.invalidate_user_cache(user_id)
            logger.info(f"Cleared search cache for user {user_id}")
        else:
            # Clear all search-related cache
            performance_optimizer.cache.clear()
            logger.info("Cleared all search cache")

# Global instance (only create if environment is properly configured)
vector_search_optimizer = None
try:
    vector_search_optimizer = VectorSearchOptimizer()
except Exception:
    # Will be None if not properly configured
    pass