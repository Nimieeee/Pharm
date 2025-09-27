-- Simple Chatbot Database Schema
-- This file contains the minimal schema needed for the simple chatbot with RAG functionality

-- Enable the pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create conversations table for multi-conversation support
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create messages table for storing chat history
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create the document_chunks table for storing processed documents
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(384), -- Sentence-transformers embedding dimension (all-MiniLM-L6-v2)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create an index for vector similarity search
-- Using ivfflat index for better performance on large datasets
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create a function for matching document chunks based on similarity
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
CREATE INDEX IF NOT EXISTS document_chunks_conversation_id_idx ON document_chunks(conversation_id);
CREATE INDEX IF NOT EXISTS messages_conversation_id_idx ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS conversations_updated_at_idx ON conversations(updated_at);

-- Add a comment to the table
COMMENT ON TABLE document_chunks IS 'Stores processed document chunks with vector embeddings for RAG functionality';
COMMENT ON COLUMN document_chunks.content IS 'The text content of the document chunk';
COMMENT ON COLUMN document_chunks.embedding IS 'Vector embedding of the content for similarity search';
COMMENT ON COLUMN document_chunks.metadata IS 'Additional metadata about the document chunk (filename, page, etc.)';
COMMENT ON FUNCTION match_document_chunks IS 'Function to find similar document chunks based on vector similarity';