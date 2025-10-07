"""
RAG (Retrieval-Augmented Generation) Service
Handles document processing and vector search using LangChain + Supabase pgvector
"""

import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
from supabase import Client
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import numpy as np

# Additional imports for document processing
try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

from app.core.config import settings
from app.models.document import DocumentChunk, DocumentChunkCreate, DocumentUploadResponse


class RAGService:
    """RAG service for document processing and retrieval using LangChain + Supabase pgvector"""
    
    def __init__(self, db: Client):
        self.db = db
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=300,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.embeddings = None
        self.vector_store = None
        self._initialize_embeddings()
        self._initialize_vector_store()
    
    def _initialize_embeddings(self):
        """Initialize HuggingFace embedding model for LangChain"""
        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name='all-MiniLM-L6-v2',
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            print("✅ LangChain embeddings initialized")
        except Exception as e:
            print(f"❌ Error initializing embeddings: {e}")
            self.embeddings = None
    
    def _initialize_vector_store(self):
        """Initialize vector store (using direct Supabase integration)"""
        try:
            # We'll use direct Supabase client instead of LangChain vector store
            # This is more reliable and doesn't require additional packages
            self.vector_store = None  # Will use direct database operations
            print("✅ Direct Supabase integration initialized")
        except Exception as e:
            print(f"❌ Error initializing vector store: {e}")
            self.vector_store = None
    
    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using HuggingFace embeddings"""
        try:
            if not self.embeddings or not text.strip():
                return None
            
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return None
    
    async def process_uploaded_file(
        self, 
        file_content: bytes, 
        filename: str, 
        conversation_id: UUID, 
        user_id: UUID
    ) -> DocumentUploadResponse:
        """Process uploaded file and store chunks using LangChain"""
        try:
            # Save file temporarily
            file_extension = filename.lower().split('.')[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                # Load document
                documents = self._load_document(tmp_file_path, filename)
                
                if not documents:
                    return DocumentUploadResponse(
                        success=False,
                        message=f"Could not process file: {filename}",
                        chunk_count=0
                    )
                
                # Split into chunks
                chunks = self.text_splitter.split_documents(documents)
                
                if not chunks:
                    return DocumentUploadResponse(
                        success=False,
                        message=f"No content found in file: {filename}",
                        chunk_count=0
                    )
                
                # Add metadata to chunks
                for chunk in chunks:
                    chunk.metadata.update({
                        "user_id": str(user_id),
                        "conversation_id": str(conversation_id),
                        "filename": filename,
                        "file_type": file_extension
                    })
                
                # Store chunks using direct database operations
                success_count = 0
                for chunk in chunks:
                    if await self._process_and_store_chunk(
                        chunk, filename, conversation_id, user_id
                    ):
                        success_count += 1
                
                return DocumentUploadResponse(
                    success=success_count > 0,
                    message=f"Processed {success_count} chunks from {filename}",
                    chunk_count=success_count
                )
                
            finally:
                # Clean up temporary file
                os.unlink(tmp_file_path)
                
        except Exception as e:
            return DocumentUploadResponse(
                success=False,
                message=f"Error processing file: {str(e)}",
                chunk_count=0
            )
    
    async def _process_and_store_chunk(
        self, 
        chunk: Document, 
        filename: str, 
        conversation_id: UUID, 
        user_id: UUID
    ) -> bool:
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
                "source": chunk.metadata.get("source", filename),
                "file_type": chunk.metadata.get("file_type", "unknown"),
                "user_id": str(user_id),
                "conversation_id": str(conversation_id)
            }
            
            # Store in database
            chunk_data = {
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
                "content": chunk.page_content,
                "embedding": embedding,
                "metadata": metadata
            }
            
            result = self.db.table("document_chunks").insert(chunk_data).execute()
            return len(result.data) > 0
            
        except Exception as e:
            print(f"❌ Error storing chunk: {e}")
            return False
    
    def _load_document(self, file_path: str, filename: str) -> List[Document]:
        """Load document based on file type"""
        try:
            file_extension = filename.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                loader = PyPDFLoader(file_path)
                return loader.load()
                
            elif file_extension in ['txt', 'md']:
                loader = TextLoader(file_path, encoding='utf-8')
                return loader.load()
                
            elif file_extension == 'docx' and DOCX_AVAILABLE:
                return self._process_docx(file_path, filename)
                
            elif file_extension == 'pptx' and PPTX_AVAILABLE:
                return self._process_pptx(file_path, filename)
                
            else:
                print(f"❌ Unsupported file type: {file_extension}")
                return []
                
        except Exception as e:
            print(f"❌ Error loading document '{filename}': {e}")
            return []
    
    def _process_docx(self, file_path: str, filename: str) -> List[Document]:
        """Process DOCX files"""
        try:
            doc = docx.Document(file_path)
            
            # Extract text from paragraphs and tables
            text_content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_content.append(cell.text.strip())
            
            if not text_content:
                return []
            
            full_text = '\n\n'.join(text_content)
            document = Document(
                page_content=full_text,
                metadata={"source": filename, "file_type": "docx"}
            )
            
            return [document]
            
        except Exception as e:
            print(f"❌ Error processing DOCX '{filename}': {e}")
            return []
    
    def _process_pptx(self, file_path: str, filename: str) -> List[Document]:
        """Process PowerPoint files"""
        try:
            prs = Presentation(file_path)
            
            text_content = []
            slide_number = 0
            
            for slide in prs.slides:
                slide_number += 1
                slide_text = []
                
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        slide_text.append(shape.text.strip())
                
                if slide_text:
                    slide_content = f"Slide {slide_number}:\n" + '\n'.join(slide_text)
                    text_content.append(slide_content)
            
            if not text_content:
                return []
            
            full_text = '\n\n'.join(text_content)
            document = Document(
                page_content=full_text,
                metadata={"source": filename, "file_type": "pptx", "slides": slide_number}
            )
            
            return [document]
            
        except Exception as e:
            print(f"❌ Error processing PowerPoint '{filename}': {e}")
            return []
    

    
    async def search_similar_chunks(
        self, 
        query: str, 
        conversation_id: UUID, 
        user_id: UUID, 
        max_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[DocumentChunk]:
        """Search for similar document chunks using direct database operations"""
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                # Fallback to recent chunks
                return await self._get_recent_chunks(conversation_id, user_id, max_results)
            
            # Search using database function
            result = self.db.rpc(
                'match_documents_with_user_isolation',
                {
                    'query_embedding': query_embedding,
                    'conversation_uuid': str(conversation_id),
                    'user_session_uuid': str(user_id),
                    'match_threshold': similarity_threshold,
                    'match_count': max_results
                }
            ).execute()
            
            chunks = []
            for row in result.data or []:
                chunk = DocumentChunk(
                    id=row['id'],
                    conversation_id=conversation_id,
                    content=row['content'],
                    metadata=row['metadata'],
                    similarity=row['similarity'],
                    created_at=row.get('created_at', '2024-01-01T00:00:00Z')
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"❌ Error searching chunks: {e}")
            # Fallback to recent chunks
            return await self._get_recent_chunks(conversation_id, user_id, max_results)
    

    
    async def _get_recent_chunks(
        self, 
        conversation_id: UUID, 
        user_id: UUID, 
        limit: int = 10
    ) -> List[DocumentChunk]:
        """Get recent chunks as fallback"""
        try:
            result = self.db.table("document_chunks").select(
                "id, content, metadata, created_at"
            ).eq("conversation_id", str(conversation_id)).eq(
                "user_id", str(user_id)
            ).order("created_at", desc=True).limit(limit).execute()
            
            chunks = []
            for row in result.data or []:
                chunk = DocumentChunk(
                    id=row['id'],
                    conversation_id=conversation_id,
                    content=row['content'],
                    metadata=row['metadata'],
                    similarity=0.5,  # Default similarity
                    created_at=row['created_at']
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"❌ Error getting recent chunks: {e}")
            return []
    
    async def get_all_conversation_chunks(
        self, 
        conversation_id: UUID, 
        user_id: UUID
    ) -> List[DocumentChunk]:
        """Get all chunks for a conversation"""
        try:
            result = self.db.table("document_chunks").select(
                "id, content, metadata, created_at"
            ).eq("conversation_id", str(conversation_id)).eq(
                "user_id", str(user_id)
            ).order("created_at").execute()
            
            chunks = []
            for row in result.data or []:
                chunk = DocumentChunk(
                    id=row['id'],
                    conversation_id=conversation_id,
                    content=row['content'],
                    metadata=row['metadata'],
                    similarity=0.5,
                    created_at=row['created_at']
                )
                chunks.append(chunk)
            
            return chunks
            
        except Exception as e:
            print(f"❌ Error getting all chunks: {e}")
            return []
    
    async def get_conversation_context(
        self, 
        query: str, 
        conversation_id: UUID, 
        user_id: UUID,
        max_chunks: int = 20
    ) -> str:
        """Get relevant context for a query"""
        try:
            # Search for relevant chunks
            chunks = await self.search_similar_chunks(
                query, conversation_id, user_id, max_chunks, 0.1
            )
            
            if not chunks:
                return ""
            
            # Organize by document
            documents = {}
            for chunk in chunks:
                filename = chunk.metadata.get("filename", "Unknown")
                if filename not in documents:
                    documents[filename] = []
                documents[filename].append(chunk.content)
            
            # Build context
            context_parts = []
            
            if len(documents) > 1:
                context_parts.append("=== DOCUMENT OVERVIEW ===")
                for filename in documents:
                    context_parts.append(f"📄 {filename} - {len(documents[filename])} sections")
                context_parts.append("")
            
            # Add content
            for filename, contents in documents.items():
                if len(documents) > 1:
                    context_parts.append(f"=== {filename} ===")
                
                for content in contents:
                    if content.strip():
                        context_parts.append(content.strip())
                
                if len(documents) > 1:
                    context_parts.append("")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            print(f"❌ Error getting context: {e}")
            return ""
    
    async def delete_conversation_documents(
        self, 
        conversation_id: UUID, 
        user_id: UUID
    ) -> bool:
        """Delete all documents for a conversation"""
        try:
            result = self.db.table("document_chunks").delete().eq(
                "conversation_id", str(conversation_id)
            ).eq("user_id", str(user_id)).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error deleting documents: {e}")
            return False