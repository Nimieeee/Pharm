-- Migration 003: Optimize database for LangChain + Supabase pgvector integration
-- This migration optimizes the existing schema for better LangChain compatibility

-- Ensure pgvector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing conflicting functions first
DROP FUNCTION IF EXISTS match_document_chunks(VECTOR(384), FLOAT, INT);
DROP FUNCTION IF EXISTS match_document_chunks(VECTOR(384), UUID, UUID, FLOAT, INT);

-- Add optimized HNSW index for better performance with LangChain
-- HNSW (Hierarchical Navigable Small World) is more efficient for similarity search
DROP INDEX IF EXISTS document_chunks_embedding_idx;
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx 
ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Keep ivfflat index as fallback for compatibility
CREATE INDEX IF NOT EXISTS document_chunks_embedding_ivf_idx 
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Add metadata indexes for LangChain filtering
CREATE INDEX IF NOT EXISTS document_chunks_metadata_user_id_idx 
ON document_chunks USING GIN ((metadata->>'user_id'));

CREATE INDEX IF NOT EXISTS document_chunks_metadata_conversation_id_idx 
ON document_chunks USING GIN ((metadata->>'conversation_id'));

CREATE INDEX IF NOT EXISTS document_chunks_metadata_filename_idx 
ON document_chunks USING GIN ((metadata->>'filename'));

-- Optimize the match_document_chunks function for LangChain
CREATE OR REPLACE FUNCTION match_document_chunks_langchain(
    query_embedding VECTOR(384),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5,
    filter_metadata JSONB DEFAULT '{}'::JSONB
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
    WHERE 
        (filter_metadata = '{}'::JSONB OR document_chunks.metadata @> filter_metadata)
        AND 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create function for LangChain similarity search with score
CREATE OR REPLACE FUNCTION similarity_search_with_score(
    query_embedding VECTOR(384),
    k INT DEFAULT 5,
    filter_metadata JSONB DEFAULT '{}'::JSONB
)
RETURNS TABLE(
    id UUID,
    content TEXT,
    metadata JSONB,
    distance FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.content,
        document_chunks.metadata,
        document_chunks.embedding <=> query_embedding AS distance
    FROM document_chunks
    WHERE 
        (filter_metadata = '{}'::JSONB OR document_chunks.metadata @> filter_metadata)
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT k;
END;
$$;

-- Add function to get embedding statistics
CREATE OR REPLACE FUNCTION get_embedding_stats()
RETURNS TABLE(
    total_chunks BIGINT,
    avg_embedding_norm FLOAT,
    min_embedding_norm FLOAT,
    max_embedding_norm FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_chunks,
        AVG(vector_norm(embedding)) as avg_embedding_norm,
        MIN(vector_norm(embedding)) as min_embedding_norm,
        MAX(vector_norm(embedding)) as max_embedding_norm
    FROM document_chunks
    WHERE embedding IS NOT NULL;
END;
$$;

-- Add comments for LangChain integration
COMMENT ON FUNCTION match_document_chunks_langchain IS 'LangChain-optimized similarity search with metadata filtering';
COMMENT ON FUNCTION similarity_search_with_score IS 'LangChain similarity search returning distance scores';
COMMENT ON FUNCTION get_embedding_stats IS 'Get statistics about stored embeddings for monitoring';
COMMENT ON INDEX document_chunks_embedding_hnsw_idx IS 'HNSW index optimized for LangChain similarity search';
COMMENT ON INDEX document_chunks_embedding_ivf_idx IS 'IVFFlat index for compatibility and fallback';

-- Create view for LangChain document retrieval
CREATE OR REPLACE VIEW langchain_documents AS
SELECT 
    id,
    content as page_content,
    metadata,
    embedding,
    created_at
FROM document_chunks
WHERE embedding IS NOT NULL;

COMMENT ON VIEW langchain_documents IS 'View optimized for LangChain document retrieval';