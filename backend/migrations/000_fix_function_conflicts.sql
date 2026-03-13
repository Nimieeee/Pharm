-- Migration 000: Fix function conflicts before running other migrations
-- This migration cleans up any existing function conflicts

-- Drop existing functions if they exist (with all possible signatures)
DROP FUNCTION IF EXISTS match_document_chunks(VECTOR(384), FLOAT, INT);
DROP FUNCTION IF EXISTS match_document_chunks(VECTOR(384), UUID, UUID, FLOAT, INT);
DROP FUNCTION IF EXISTS match_document_chunks_langchain(VECTOR(384), FLOAT, INT, JSONB);
DROP FUNCTION IF EXISTS similarity_search_with_score(VECTOR(384), INT, JSONB);
DROP FUNCTION IF EXISTS get_conversation_stats(UUID, UUID);
DROP FUNCTION IF EXISTS get_embedding_stats();

-- Drop existing indexes that might conflict
DROP INDEX IF EXISTS document_chunks_embedding_idx;
DROP INDEX IF EXISTS document_chunks_embedding_hnsw_idx;
DROP INDEX IF EXISTS document_chunks_embedding_ivf_idx;

-- Drop existing view if it exists
DROP VIEW IF EXISTS langchain_documents;

-- Ensure pgvector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;