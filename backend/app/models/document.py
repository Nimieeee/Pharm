"""
Document and RAG data models
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel


class DocumentChunkBase(BaseModel):
    """Base document chunk model"""
    content: str
    metadata: Dict[str, Any] = {}


class DocumentChunkCreate(DocumentChunkBase):
    """Document chunk creation model"""
    conversation_id: UUID
    embedding: List[float]


class DocumentChunkInDB(DocumentChunkBase):
    """Document chunk model as stored in database"""
    id: UUID
    conversation_id: UUID
    user_id: UUID
    embedding: List[float]
    created_at: datetime
    
    class Config:
        orm_mode = True


class DocumentChunk(DocumentChunkBase):
    """Document chunk model for API responses"""
    id: UUID
    conversation_id: UUID
    created_at: datetime
    similarity: Optional[float] = None  # For search results
    
    class Config:
        orm_mode = True


class DocumentUpload(BaseModel):
    """Document upload request"""
    filename: str
    content_type: str
    size: int


class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    success: bool
    message: str
    chunk_count: int = 0
    document_id: Optional[str] = None
    processing_time: Optional[float] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    file_info: Optional[Dict[str, Any]] = None


class DocumentSearchRequest(BaseModel):
    """Document search request"""
    query: str
    conversation_id: UUID
    max_results: int = 10
    similarity_threshold: float = 0.7


class DocumentSearchResponse(BaseModel):
    """Document search response"""
    chunks: List[DocumentChunk]
    total_results: int
    query: str