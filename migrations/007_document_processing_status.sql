-- Migration 007: Add document processing status tracking
-- This migration adds document processing status tracking functionality

-- Create document processing status table
CREATE TABLE IF NOT EXISTS document_processing_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    file_size BIGINT,
    mime_type TEXT,
    status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed', 'queued')),
    chunks_created INTEGER DEFAULT 0,
    embeddings_stored INTEGER DEFAULT 0,
    error_message TEXT,
    processing_started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient document processing queries
CREATE INDEX IF NOT EXISTS idx_document_processing_user_id ON document_processing_status(user_id);
CREATE INDEX IF NOT EXISTS idx_document_processing_status ON document_processing_status(status);
CREATE INDEX IF NOT EXISTS idx_document_processing_user_status ON document_processing_status(user_id, status);
CREATE INDEX IF NOT EXISTS idx_document_processing_created_at ON document_processing_status(created_at DESC);

-- Enable Row Level Security on document_processing_status table
ALTER TABLE document_processing_status ENABLE ROW LEVEL SECURITY;

-- Document processing status RLS policies
-- Users can only access their own document processing records
CREATE POLICY "Users can view own document processing status" ON document_processing_status
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own document processing status" ON document_processing_status
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own document processing status" ON document_processing_status
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own document processing status" ON document_processing_status
    FOR DELETE USING (auth.uid() = user_id);

-- Function to update document processing status updated_at timestamp
CREATE OR REPLACE FUNCTION update_document_processing_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    
    -- Set processing_completed_at when status changes to completed or failed
    IF NEW.status IN ('completed', 'failed') AND OLD.status NOT IN ('completed', 'failed') THEN
        NEW.processing_completed_at = NOW();
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update document processing status timestamp
CREATE TRIGGER update_document_processing_status_timestamp
    BEFORE UPDATE ON document_processing_status
    FOR EACH ROW
    EXECUTE FUNCTION update_document_processing_timestamp();

-- Function to get user document processing status with summary
CREATE OR REPLACE FUNCTION get_user_document_processing_status(user_id UUID)
RETURNS TABLE(
    id UUID,
    filename TEXT,
    original_filename TEXT,
    file_size BIGINT,
    mime_type TEXT,
    status TEXT,
    chunks_created INTEGER,
    embeddings_stored INTEGER,
    error_message TEXT,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_duration INTERVAL
)
LANGUAGE SQL STABLE
AS $$
    SELECT 
        dps.id,
        dps.filename,
        dps.original_filename,
        dps.file_size,
        dps.mime_type,
        dps.status,
        dps.chunks_created,
        dps.embeddings_stored,
        dps.error_message,
        dps.processing_started_at,
        dps.processing_completed_at,
        CASE 
            WHEN dps.processing_completed_at IS NOT NULL 
            THEN dps.processing_completed_at - dps.processing_started_at
            ELSE NULL
        END as processing_duration
    FROM document_processing_status dps
    WHERE dps.user_id = get_user_document_processing_status.user_id
    ORDER BY dps.created_at DESC;
$$;

-- Function to get document processing summary for a user
CREATE OR REPLACE FUNCTION get_document_processing_summary(user_id UUID)
RETURNS TABLE(
    total_documents INTEGER,
    processing_documents INTEGER,
    completed_documents INTEGER,
    failed_documents INTEGER,
    total_chunks INTEGER,
    total_embeddings INTEGER
)
LANGUAGE SQL STABLE
AS $$
    SELECT 
        COUNT(*)::INTEGER as total_documents,
        COUNT(CASE WHEN status = 'processing' OR status = 'queued' THEN 1 END)::INTEGER as processing_documents,
        COUNT(CASE WHEN status = 'completed' THEN 1 END)::INTEGER as completed_documents,
        COUNT(CASE WHEN status = 'failed' THEN 1 END)::INTEGER as failed_documents,
        COALESCE(SUM(chunks_created), 0)::INTEGER as total_chunks,
        COALESCE(SUM(embeddings_stored), 0)::INTEGER as total_embeddings
    FROM document_processing_status dps
    WHERE dps.user_id = get_document_processing_summary.user_id;
$$;

-- Function to cleanup old document processing records (optional maintenance)
CREATE OR REPLACE FUNCTION cleanup_old_document_processing_records(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM document_processing_status 
    WHERE created_at < NOW() - INTERVAL '1 day' * days_to_keep
    AND status IN ('completed', 'failed');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;