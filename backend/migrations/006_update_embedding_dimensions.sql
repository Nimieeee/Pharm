-- Migration: Update embedding dimensions from 384 to 1024 for Mistral embeddings
-- This migration updates the vector column to support Mistral's 1024-dimensional embeddings

-- Step 1: Drop existing vector column and recreate with new dimensions
ALTER TABLE document_chunks 
DROP COLUMN IF EXISTS embedding;

-- Step 2: Add new embedding column with 1024 dimensions
ALTER TABLE document_chunks 
ADD COLUMN embedding vector(1024);

-- Step 3: Create index for vector similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Step 4: Update the match function to use 1024 dimensions
CREATE OR REPLACE FUNCTION match_documents_with_user_isolation(
  query_embedding vector(1024),
  conversation_uuid uuid,
  user_session_uuid uuid,
  match_threshold float DEFAULT 0.1,
  match_count int DEFAULT 10
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
    document_chunks.id,
    document_chunks.content,
    document_chunks.metadata,
    1 - (document_chunks.embedding <=> query_embedding) as similarity
  FROM document_chunks
  WHERE 
    document_chunks.conversation_id = conversation_uuid
    AND document_chunks.user_id = user_session_uuid
    AND 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
  ORDER BY document_chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Note: This will delete all existing embeddings!
-- Run this migration when you're ready to switch to Mistral embeddings.
-- After running this, you'll need to re-upload all documents.
