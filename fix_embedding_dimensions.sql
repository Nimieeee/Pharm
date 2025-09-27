-- Fix embedding dimensions from 1536 to 384 for sentence-transformers
-- Run this in your Supabase SQL Editor to fix the dimension mismatch

-- Enable the pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop the existing function first (with correct signature)
DROP FUNCTION IF EXISTS match_document_chunks(vector, float, int);

-- Drop the existing table to recreate with correct dimensions
DROP TABLE IF EXISTS document_chunks;

-- Recreate the table with correct embedding dimensions (matching the schema exactly)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding VECTOR(384), -- Sentence-transformers embedding dimension (all-MiniLM-L6-v2)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create an index for vector similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Recreate the function with correct dimensions (matching the exact schema)
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding VECTOR(384),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE(
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.content,
        document_chunks.metadata,
        1 - (document_chunks.embedding <=> query_embedding) AS similarity
    FROM document_chunks
    WHERE 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS document_chunks_created_at_idx ON document_chunks(created_at);
CREATE INDEX IF NOT EXISTS document_chunks_metadata_idx ON document_chunks USING GIN(metadata);

-- Add comments
COMMENT ON TABLE document_chunks IS 'Stores processed document chunks with vector embeddings for RAG functionality';
COMMENT ON COLUMN document_chunks.content IS 'The text content of the document chunk';
COMMENT ON COLUMN document_chunks.embedding IS 'Vector embedding (384 dimensions) using sentence-transformers all-MiniLM-L6-v2';
COMMENT ON COLUMN document_chunks.metadata IS 'Additional metadata about the document chunk (filename, page, etc.)';
COMMENT ON FUNCTION match_document_chunks IS 'Function to find similar document chunks based on vector similarity';

-- Verify the fix
SELECT 'Embedding dimensions fixed: 1536 -> 384' as status;