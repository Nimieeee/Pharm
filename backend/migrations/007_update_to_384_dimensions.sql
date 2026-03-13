-- Migration: Update embedding dimensions from 1024 to 384 for Sentence Transformers
-- Model: all-MiniLM-L6-v2 (384 dimensions)
-- This migration updates the vector column to use 384 dimensions

-- Drop existing index
DROP INDEX IF EXISTS document_chunks_embedding_idx;

-- Alter the embedding column to 384 dimensions
ALTER TABLE document_chunks 
ALTER COLUMN embedding TYPE vector(384);

-- Recreate the index for similarity search
CREATE INDEX document_chunks_embedding_idx ON document_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Note: Existing embeddings will need to be regenerated
-- They are now invalid due to dimension mismatch
-- Consider truncating the table or regenerating embeddings:
-- TRUNCATE TABLE document_chunks;
