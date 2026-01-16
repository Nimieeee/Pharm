-- Migration: Revert embedding dimensions back to 1024 for Mistral embeddings
-- The system was using 768 (Nomic) but Mistral API returns 1024 dimension embeddings
-- This migration updates the vector column and functions to use 1024 dimensions

-- Drop existing embedding column and recreate with 1024 dimensions
ALTER TABLE document_chunks DROP COLUMN IF EXISTS embedding;
ALTER TABLE document_chunks ADD COLUMN embedding vector(1024);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Update the match_documents function
CREATE OR REPLACE FUNCTION match_documents_with_user_isolation(
  query_embedding vector(1024),
  query_user_id uuid,
  query_conversation_id uuid,
  match_threshold float DEFAULT 0.05,
  match_count int DEFAULT 20
)
RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.content,
    dc.metadata,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM document_chunks dc
  WHERE dc.user_id = query_user_id
    AND dc.conversation_id = query_conversation_id
    AND dc.embedding IS NOT NULL
    AND 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
