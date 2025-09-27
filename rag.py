"""
RAG (Retrieval-Augmented Generation) System
Handles document processing and vector search using Langchain
"""

import os
from typing import List, Dict, Any, Optional
import streamlit as st
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
import tempfile
import numpy as np

from database import SimpleChatbotDB


class RAGManager:
    """Manages document processing and retrieval for RAG system"""
    
    def __init__(self):
        self.db_manager = SimpleChatbotDB()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        self.embedding_model = None
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize embedding model"""
        try:
            # Try to use OpenAI embeddings if available
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                self.embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)
            else:
                # Fallback to sentence transformers
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                
        except Exception as e:
            st.error(f"Error initializing embeddings: {str(e)}")
            # Fallback to sentence transformers
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as fallback_e:
                st.error(f"Fallback embedding initialization failed: {str(fallback_e)}")
    
    def process_uploaded_file(self, uploaded_file, progress_callback=None) -> tuple[bool, int]:
        """
        Process uploaded file and store chunks in database with enhanced feedback
        
        Args:
            uploaded_file: Streamlit uploaded file object
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success: bool, chunk_count: int)
        """
        try:
            if not uploaded_file:
                return False, 0
            
            if progress_callback:
                progress_callback("Saving temporary file...")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            if progress_callback:
                progress_callback("Loading document...")
            
            # Load document based on file type
            documents = self._load_document(tmp_file_path, uploaded_file.name)
            
            if not documents:
                os.unlink(tmp_file_path)
                return False, 0
            
            if progress_callback:
                progress_callback("Splitting into chunks...")
            
            # Split documents into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            if not chunks:
                st.error(f"No chunks created from '{uploaded_file.name}' - document may be empty or unreadable")
                os.unlink(tmp_file_path)
                return False, 0
            
            if progress_callback:
                progress_callback(f"Processing {len(chunks)} chunks...")
            
            # Process and store chunks with progress tracking
            success_count = 0
            for i, chunk in enumerate(chunks):
                # Check if chunk has content
                if not chunk.page_content.strip():
                    continue
                
                if self._process_and_store_chunk(chunk, uploaded_file.name):
                    success_count += 1
            
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
            return success_count > 0, success_count
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return False, 0
    
    def _load_document(self, file_path: str, filename: str) -> List[Document]:
        """Load document based on file type with enhanced support and debugging"""
        try:
            file_extension = filename.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                loader = PyPDFLoader(file_path)
                documents = loader.load()
                if not documents:
                    st.warning(f"PDF '{filename}' loaded but contains no readable content")
                return documents
                
            elif file_extension in ['txt', 'md']:
                loader = TextLoader(file_path, encoding='utf-8')
                documents = loader.load()
                if not documents:
                    st.warning(f"Text file '{filename}' loaded but contains no content")
                return documents
                
            elif file_extension == 'docx':
                # Process DOCX silently
                try:
                    import docx
                except ImportError:
                    return []
                
                # Process the document
                try:
                    doc = docx.Document(file_path)
                    
                    # Extract text from all paragraphs
                    text_content = []
                    for paragraph in doc.paragraphs:
                        if paragraph.text.strip():
                            text_content.append(paragraph.text.strip())
                    
                    # Extract text from tables
                    for table in doc.tables:
                        for row in table.rows:
                            for cell in row.cells:
                                if cell.text.strip():
                                    text_content.append(cell.text.strip())
                    
                    if not text_content:
                        return []
                    
                    # Create a Document object
                    full_text = '\n\n'.join(text_content)
                    document = Document(
                        page_content=full_text,
                        metadata={"source": filename, "file_type": "docx"}
                    )
                    
                    return [document]
                    
                except Exception as docx_error:
                    st.error(f"❌ Error processing DOCX '{filename}': {str(docx_error)}")
                    st.info("💡 Try converting the DOCX to PDF or TXT format")
                    return []
                    
            else:
                st.error(f"Unsupported file type: {file_extension}. Supported types: PDF, TXT, MD, DOCX")
                return []
                
        except Exception as e:
            st.error(f"Error loading document '{filename}': {str(e)}")
            return []
    
    def _process_and_store_chunk(self, chunk: Document, filename: str) -> bool:
        """Process chunk and store in database"""
        try:
            # Generate embedding
            embedding = self._generate_embedding(chunk.page_content)
            if not embedding:
                return False
            
            # Prepare metadata
            metadata = {
                "filename": filename,
                "page": chunk.metadata.get("page", 0),
                "source": chunk.metadata.get("source", filename)
            }
            
            # Store in database
            return self.db_manager.store_document_chunk(
                content=chunk.page_content,
                embedding=embedding,
                metadata=metadata
            )
            
        except Exception as e:
            st.error(f"Error processing chunk: {str(e)}")
            return False
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text with detailed error handling"""
        try:
            if not self.embedding_model:
                st.error("Embedding model not initialized. Check your configuration.")
                return None
            
            if not text or not text.strip():
                st.warning("Cannot generate embedding for empty text")
                return None
            
            if hasattr(self.embedding_model, 'embed_query'):
                # OpenAI embeddings
                embedding = self.embedding_model.embed_query(text)
            else:
                # Sentence transformers
                embedding = self.embedding_model.encode(text).tolist()
            
            if not embedding or len(embedding) == 0:
                st.error("Generated embedding is empty")
                return None
            
            return embedding
            
        except Exception as e:
            st.error(f"Error generating embedding: {str(e)}")
            if "api" in str(e).lower():
                st.info("💡 Check your OpenAI API key or try using sentence-transformers")
            return None
    
    def search_relevant_context(self, query: str, max_chunks: int = 3) -> str:
        """
        Search for relevant context based on query
        
        Args:
            query: User query
            max_chunks: Maximum number of chunks to retrieve
            
        Returns:
            Concatenated relevant context
        """
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                return ""
            
            # Search for similar chunks with lower threshold
            similar_chunks = self.db_manager.search_similar_chunks(query_embedding, max_chunks, threshold=0.3)
            
            if not similar_chunks:
                return ""
            
            # Concatenate relevant content
            context_parts = []
            for chunk in similar_chunks:
                content = chunk.get("content", "")
                if content:
                    context_parts.append(content)
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            st.error(f"Error searching context: {str(e)}")
            return ""
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about stored documents"""
        try:
            chunk_count = self.db_manager.get_chunk_count()
            document_info = self.db_manager.get_document_info()
            
            return {
                "total_chunks": chunk_count,
                "embedding_model": type(self.embedding_model).__name__ if self.embedding_model else "None",
                "unique_documents": document_info.get("unique_documents", 0),
                "total_size_mb": document_info.get("total_size_mb", 0),
                "last_updated": document_info.get("last_updated", "Never")
            }
            
        except Exception as e:
            st.error(f"Error getting document stats: {str(e)}")
            return {
                "total_chunks": 0, 
                "embedding_model": "Error",
                "unique_documents": 0,
                "total_size_mb": 0,
                "last_updated": "Error"
            }
    
    def clear_all_documents(self) -> bool:
        """Clear all stored documents"""
        try:
            return self.db_manager.clear_all_chunks()
        except Exception as e:
            st.error(f"Error clearing documents: {str(e)}")
            return False
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status"""
        return getattr(st.session_state, 'processing_status', {
            'active': False,
            'progress': 0,
            'current_file': '',
            'total_files': 0,
            'processed_files': 0
        })