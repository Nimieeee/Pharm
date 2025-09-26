# document_processor.py
import os
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import streamlit as st

try:
    from supabase import create_client
except ImportError:
    create_client = None

from embeddings import get_embeddings
from ingestion import (
    extract_text_from_file, 
    chunk_texts, 
    extract_text_from_url
)

@dataclass
class ProcessedDocument:
    """Processed document with user association"""
    id: str
    user_id: str
    content: str
    source: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class DocumentProcessor:
    """Enhanced document processor with user ID association"""
    
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
    
    def process_uploaded_files(
        self, 
        uploaded_files: List, 
        user_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[ProcessedDocument]:
        """
        Process uploaded files and associate them with user ID
        
        Args:
            uploaded_files: List of uploaded file objects
            user_id: User ID to associate documents with
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of ProcessedDocument objects
        """
        processed_docs = []
        
        for uploaded_file in uploaded_files:
            try:
                # Extract text from file
                text = extract_text_from_file(uploaded_file)
                if not text.strip():
                    continue
                
                # Get file name
                source_name = getattr(uploaded_file, 'name', 'uploaded_file')
                
                # Create chunks
                chunks = chunk_texts(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
                
                # Process each chunk
                for i, chunk in enumerate(chunks):
                    doc_id = f"{user_id}-{source_name}-{i}-{uuid.uuid4().hex[:8]}"
                    
                    processed_doc = ProcessedDocument(
                        id=doc_id,
                        user_id=user_id,
                        content=chunk,
                        source=source_name,
                        metadata={
                            'chunk_index': i,
                            'total_chunks': len(chunks),
                            'file_type': self._get_file_type(source_name),
                            'upload_timestamp': str(uuid.uuid1().time)
                        }
                    )
                    processed_docs.append(processed_doc)
                    
            except Exception as e:
                print(f"Error processing file {getattr(uploaded_file, 'name', 'unknown')}: {e}")
                continue
        
        return processed_docs
    
    def process_url_content(
        self, 
        url: str, 
        user_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[ProcessedDocument]:
        """
        Process content from URL and associate with user ID
        
        Args:
            url: URL to extract content from
            user_id: User ID to associate documents with
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of ProcessedDocument objects
        """
        try:
            # Extract text from URL
            text = extract_text_from_url(url)
            if not text.strip():
                return []
            
            # Create chunks
            chunks = chunk_texts(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            
            processed_docs = []
            for i, chunk in enumerate(chunks):
                doc_id = f"{user_id}-url-{i}-{uuid.uuid4().hex[:8]}"
                
                processed_doc = ProcessedDocument(
                    id=doc_id,
                    user_id=user_id,
                    content=chunk,
                    source=url,
                    metadata={
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'content_type': 'url',
                        'url': url,
                        'upload_timestamp': str(uuid.uuid1().time)
                    }
                )
                processed_docs.append(processed_doc)
            
            return processed_docs
            
        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            return []
    
    def store_documents(self, documents: List[ProcessedDocument]) -> bool:
        """
        Store processed documents in Supabase with embeddings using batching for memory efficiency
        
        Args:
            documents: List of ProcessedDocument objects to store
            
        Returns:
            True if successful, False otherwise
        """
        if not documents:
            return True
        
        try:
            # Process documents in smaller batches to manage memory
            batch_size = 5  # Even smaller batches for better memory management
            total_stored = 0
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Generate embeddings for batch with error handling
                texts = [doc.content[:2000] for doc in batch]  # Limit text length
                try:
                    embeddings = self.embedding_model.embed_documents(texts)
                except Exception as e:
                    print(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                    continue
                
                # Prepare rows for insertion with validation
                rows = []
                for doc, embedding in zip(batch, embeddings):
                    # Validate embedding dimension
                    if len(embedding) != 384:
                        print(f"Warning: Embedding dimension mismatch for doc {doc.id}")
                        continue
                        
                    row = {
                        'id': doc.id,
                        'user_id': doc.user_id,
                        'content': doc.content,
                        'source': doc.source,
                        'metadata': doc.metadata,
                        'embedding': embedding
                    }
                    rows.append(row)
                
                # Insert batch into database with error handling
                if rows:
                    try:
                        result = self.supabase_client.table('documents').upsert(rows).execute()
                        total_stored += len(result.data) if result.data else 0
                    except Exception as e:
                        print(f"Error inserting batch {i//batch_size + 1}: {e}")
                        continue
                
                # Clear batch data from memory
                del texts, embeddings, rows
            
            return total_stored > 0
            
        except Exception as e:
            print(f"Error storing documents: {e}")
            return False
    
    def delete_user_documents(self, user_id: str, source: Optional[str] = None) -> bool:
        """
        Delete documents for a user, optionally filtered by source
        
        Args:
            user_id: User ID whose documents to delete
            source: Optional source filter
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = self.supabase_client.table('documents').delete().eq('user_id', user_id)
            
            if source:
                query = query.eq('source', source)
            
            result = query.execute()
            return True
            
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from filename"""
        filename_lower = filename.lower()
        if filename_lower.endswith('.pdf'):
            return 'pdf'
        elif filename_lower.endswith('.docx'):
            return 'docx'
        elif filename_lower.endswith(('.html', '.htm')):
            return 'html'
        elif filename_lower.endswith('.txt'):
            return 'text'
        else:
            return 'unknown'