# vector_retriever.py
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import streamlit as st

try:
    from supabase import create_client
except ImportError:
    create_client = None

from embeddings import get_embeddings

@dataclass
class Document:
    """Document model for RAG pipeline"""
    id: str
    content: str
    source: str
    metadata: Dict[str, Any]
    similarity: Optional[float] = None

class VectorRetriever:
    """Enhanced vector retriever with user-scoped document filtering"""
    
    def __init__(self, supabase_client=None, embedding_model=None):
        self.supabase_client = supabase_client or self._get_supabase_client()
        self.embedding_model = embedding_model or get_embeddings()
    
    def _get_supabase_client(self):
        """Initialize Supabase client"""
        if create_client is None:
            raise ImportError("Supabase client not available. Install supabase package.")
        
        # Try to get from Streamlit secrets first, then environment
        try:
            url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_ANON_KEY")
        except:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment or Streamlit secrets")
        return create_client(url, key)
    
    def similarity_search(
        self, 
        query: str, 
        user_id: str,
        k: int = 5, 
        similarity_threshold: float = 0.1
    ) -> List[Document]:
        """
        Perform user-scoped similarity search using pgvector with memory optimization
        
        Args:
            query: Search query text
            user_id: User ID for filtering documents
            k: Number of documents to retrieve
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            List of Document objects with similarity scores
        """
        try:
            # Limit k to prevent excessive memory usage
            k = min(k, 5)
            
            # Generate query embedding with error handling
            try:
                query_embedding = self.embedding_model.embed_query(query)
            except Exception as e:
                print(f"Error generating query embedding: {e}")
                return []
            
            # Validate embedding dimension
            if len(query_embedding) != 384:
                print(f"Warning: Query embedding dimension mismatch: {len(query_embedding)}")
                return []
            
            # Use the user-scoped vector search function with error handling
            try:
                result = self.supabase_client.rpc(
                    'match_documents',
                    {
                        'user_id': user_id,
                        'query_embedding': query_embedding,
                        'match_threshold': similarity_threshold,
                        'match_count': k
                    }
                ).execute()
            except Exception as e:
                print(f"Error in vector search RPC call: {e}")
                # Fallback to basic text search if vector search fails
                return self._fallback_text_search(query, user_id, k)
            
            # Convert results to Document objects with memory-efficient processing
            documents = []
            if result.data:
                for row in result.data:
                    # Truncate content if too long to save memory
                    content = row.get('content', '')
                    if len(content) > 1500:
                        content = content[:1500] + "..."
                    
                    doc = Document(
                        id=row.get('id', ''),
                        content=content,
                        source=row.get('source', ''),
                        metadata=row.get('metadata', {}),
                        similarity=row.get('similarity', 0.0)
                    )
                    documents.append(doc)
            
            # Clear the query embedding from memory
            del query_embedding
            
            return documents
            
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []
    
    def _fallback_text_search(self, query: str, user_id: str, k: int) -> List[Document]:
        """Fallback text-based search when vector search fails"""
        try:
            # Simple text search using PostgreSQL's text search capabilities
            query_words = query.lower().split()
            search_terms = ' | '.join(query_words[:3])  # Limit to first 3 words
            
            result = self.supabase_client.table('documents')\
                .select('id, content, source, metadata')\
                .eq('user_id', user_id)\
                .text_search('content', search_terms)\
                .limit(k)\
                .execute()
            
            documents = []
            if result.data:
                for row in result.data:
                    content = row.get('content', '')
                    if len(content) > 1500:
                        content = content[:1500] + "..."
                    
                    doc = Document(
                        id=row.get('id', ''),
                        content=content,
                        source=row.get('source', ''),
                        metadata=row.get('metadata', {}),
                        similarity=0.5  # Default similarity for text search
                    )
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Error in fallback text search: {e}")
            return []
    
    def get_user_document_count(self, user_id: str) -> int:
        """Get the total number of documents for a user"""
        try:
            result = self.supabase_client.rpc(
                'get_user_document_count',
                {'user_id': user_id}
            ).execute()
            return result.data or 0
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0
    
    def get_user_documents(
        self, 
        user_id: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Document]:
        """Retrieve all documents for a user with pagination"""
        try:
            result = self.supabase_client.table('documents')\
                .select('id, content, source, metadata, created_at')\
                .eq('user_id', user_id)\
                .order('created_at', desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            documents = []
            for row in result.data:
                doc = Document(
                    id=row['id'],
                    content=row['content'],
                    source=row['source'],
                    metadata=row.get('metadata', {})
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Error retrieving user documents: {e}")
            return []