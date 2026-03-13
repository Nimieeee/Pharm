-- Migration: Update embedding dimensions 1024 -> 768 for Nomic Embed Text v1.5
-- This migration updates the vector column to support Nomic's 768-dimensional embeddings

-- Step 1: Drop dependent view first (if exists)
DROP VIEW IF EXISTS langchain_documents CASCADE;

-- Step 2: Drop existing vector column and recreate with new dimensions
ALTER TABLE document_chunks 
DROP COLUMN IF EXISTS embedding CASCADE;

-- Step 3: Add new embedding column with 768 dimensions
ALTER TABLE document_chunks 
ADD COLUMN embedding vector(768);

-- Step 4: Create index for vector similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Step 5: Update the match function to use 768 dimensions
-- Dropping first to handle signature change cleanly
DROP FUNCTION IF EXISTS match_documents(vector(1024), float, int);
DROP FUNCTION IF EXISTS match_documents_with_user_isolation(vector(1024), uuid, uuid, float, int);

CREATE OR REPLACE FUNCTION match_documents_with_user_isolation(
  query_embedding vector(768),
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

-- IMPORTANT: Legacy function support if older code uses it
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(768),
  match_threshold float,
  match_count int
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
  WHERE 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
  ORDER BY document_chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
