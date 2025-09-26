# document_processing_status.py
import os
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import streamlit as st

try:
    from supabase import create_client
except ImportError:
    create_client = None

@dataclass
class DocumentProcessingStatus:
    """Document processing status model"""
    id: str
    user_id: str
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    status: str  # 'queued', 'processing', 'completed', 'failed'
    chunks_created: int = 0
    embeddings_stored: int = 0
    error_message: Optional[str] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class ProcessingSummary:
    """Summary of document processing for a user"""
    total_documents: int
    processing_documents: int
    completed_documents: int
    failed_documents: int
    total_chunks: int
    total_embeddings: int

class DocumentProcessingStatusManager:
    """Manages document processing status tracking"""
    
    def __init__(self, supabase_client=None):
        self.supabase_client = supabase_client or self._get_supabase_client()
    
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
    
    def create_processing_record(
        self, 
        user_id: str, 
        filename: str, 
        original_filename: str,
        file_size: int,
        mime_type: str
    ) -> str:
        """
        Create a new document processing record
        
        Args:
            user_id: User ID
            filename: Processed filename
            original_filename: Original uploaded filename
            file_size: File size in bytes
            mime_type: MIME type of the file
            
        Returns:
            Processing record ID
        """
        try:
            record_id = str(uuid.uuid4())
            
            record = {
                'id': record_id,
                'user_id': user_id,
                'filename': filename,
                'original_filename': original_filename,
                'file_size': file_size,
                'mime_type': mime_type,
                'status': 'queued',
                'chunks_created': 0,
                'embeddings_stored': 0,
                'processing_started_at': datetime.now().isoformat()
            }
            
            result = self.supabase_client.table('document_processing_status').insert(record).execute()
            
            if result.data:
                return record_id
            else:
                raise Exception("Failed to create processing record")
                
        except Exception as e:
            print(f"Error creating processing record: {e}")
            return record_id  # Return ID even if database fails
    
    def update_status(
        self, 
        record_id: str, 
        status: str, 
        chunks_created: Optional[int] = None,
        embeddings_stored: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update processing status
        
        Args:
            record_id: Processing record ID
            status: New status ('processing', 'completed', 'failed')
            chunks_created: Number of chunks created
            embeddings_stored: Number of embeddings stored
            error_message: Error message if failed
            
        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {'status': status}
            
            if status == 'processing':
                update_data['processing_started_at'] = datetime.now().isoformat()
            elif status in ['completed', 'failed']:
                update_data['processing_completed_at'] = datetime.now().isoformat()
            
            if chunks_created is not None:
                update_data['chunks_created'] = chunks_created
            
            if embeddings_stored is not None:
                update_data['embeddings_stored'] = embeddings_stored
            
            if error_message is not None:
                update_data['error_message'] = error_message
            
            result = self.supabase_client.table('document_processing_status')\
                .update(update_data)\
                .eq('id', record_id)\
                .execute()
            
            return bool(result.data)
            
        except Exception as e:
            print(f"Error updating processing status: {e}")
            return False
    
    def get_user_processing_status(self, user_id: str) -> List[DocumentProcessingStatus]:
        """
        Get all processing records for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of DocumentProcessingStatus objects
        """
        try:
            result = self.supabase_client.rpc(
                'get_user_document_processing_status',
                {'user_id': user_id}
            ).execute()
            
            records = []
            if result.data:
                for row in result.data:
                    record = DocumentProcessingStatus(
                        id=row['id'],
                        user_id=user_id,
                        filename=row['filename'],
                        original_filename=row['original_filename'],
                        file_size=row.get('file_size', 0),
                        mime_type=row.get('mime_type', ''),
                        status=row['status'],
                        chunks_created=row.get('chunks_created', 0),
                        embeddings_stored=row.get('embeddings_stored', 0),
                        error_message=row.get('error_message'),
                        processing_started_at=row.get('processing_started_at'),
                        processing_completed_at=row.get('processing_completed_at')
                    )
                    records.append(record)
            
            return records
            
        except Exception as e:
            print(f"Error getting processing status: {e}")
            return []
    
    def get_processing_summary(self, user_id: str) -> ProcessingSummary:
        """
        Get processing summary for a user
        
        Args:
            user_id: User ID
            
        Returns:
            ProcessingSummary object
        """
        try:
            result = self.supabase_client.rpc(
                'get_document_processing_summary',
                {'user_id': user_id}
            ).execute()
            
            if result.data and len(result.data) > 0:
                data = result.data[0]
                return ProcessingSummary(
                    total_documents=data.get('total_documents', 0),
                    processing_documents=data.get('processing_documents', 0),
                    completed_documents=data.get('completed_documents', 0),
                    failed_documents=data.get('failed_documents', 0),
                    total_chunks=data.get('total_chunks', 0),
                    total_embeddings=data.get('total_embeddings', 0)
                )
            else:
                return ProcessingSummary(0, 0, 0, 0, 0, 0)
                
        except Exception as e:
            print(f"Error getting processing summary: {e}")
            return ProcessingSummary(0, 0, 0, 0, 0, 0)
    
    def cleanup_old_records(self, days_to_keep: int = 30) -> int:
        """
        Clean up old processing records
        
        Args:
            days_to_keep: Number of days to keep records
            
        Returns:
            Number of records deleted
        """
        try:
            result = self.supabase_client.rpc(
                'cleanup_old_document_processing_records',
                {'days_to_keep': days_to_keep}
            ).execute()
            
            return result.data or 0
            
        except Exception as e:
            print(f"Error cleaning up old records: {e}")
            return 0