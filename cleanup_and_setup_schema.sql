-- Complete Database Schema Setup with Cleanup
-- This script will clean up any existing functions and set up the complete schema

-- Enable the pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop all existing versions of the function to avoid conflicts
DROP FUNCTION IF EXISTS match_document_chunks(VECTOR(384), FLOAT, INT);
DROP FUNCTION IF EXISTS match_document_chunks(VECTOR(384), UUID, FLOAT, INT);
DROP FUNCTION IF EXISTS get_conversation_stats(UUID);

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

-- Check if document_chunks table exists and has conversation_id column
DO $$
BEGIN
    -- Check if table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'document_chunks') THEN
        -- Check if conversation_id column exists
        IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_name = 'document_chunks' AND column_name = 'conversation_id') THEN
            -- Add conversation_id column to existing table
            ALTER TABLE document_chunks ADD COLUMN conversation_id UUID;
            -- You may need to populate this column with a default conversation ID
            -- or migrate existing data as needed
        END IF;
    ELSE
        -- Create new table with conversation_id
        CREATE TABLE document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            embedding VECTOR(384), -- Sentence-transformers embedding dimension (all-MiniLM-L6-v2)
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    END IF;
END
$$;

-- Create an index for vector similarity search
-- Using ivfflat index for better performance on large datasets
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS document_chunks_created_at_idx ON document_chunks(created_at);
CREATE INDEX IF NOT EXISTS document_chunks_metadata_idx ON document_chunks USING GIN(metadata);
CREATE INDEX IF NOT EXISTS document_chunks_conversation_id_idx ON document_chunks(conversation_id);
CREATE INDEX IF NOT EXISTS messages_conversation_id_idx ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS conversations_updated_at_idx ON conversations(updated_at);

-- Create the conversation-aware match function
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding VECTOR(384),
    conversation_uuid UUID,
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
    WHERE document_chunks.conversation_id = conversation_uuid
    AND 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create a function to get conversation statistics
CREATE OR REPLACE FUNCTION get_conversation_stats(conversation_uuid UUID)
RETURNS TABLE(
    message_count BIGINT,
    document_count BIGINT,
    last_activity TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        (SELECT COUNT(*) FROM messages WHERE conversation_id = conversation_uuid) as message_count,
        (SELECT COUNT(DISTINCT metadata->>'filename') FROM document_chunks WHERE conversation_id = conversation_uuid) as document_count,
        (SELECT GREATEST(
            COALESCE(MAX(created_at), '1970-01-01'::timestamptz) 
        ) FROM (
            SELECT created_at FROM messages WHERE conversation_id = conversation_uuid
            UNION ALL
            SELECT created_at FROM document_chunks WHERE conversation_id = conversation_uuid
        ) as activities) as last_activity;
END;
$$;

-- Add comments
COMMENT ON TABLE conversations IS 'Stores conversation metadata for multi-conversation support';
COMMENT ON TABLE messages IS 'Stores chat messages for each conversation';
COMMENT ON TABLE document_chunks IS 'Stores processed document chunks with vector embeddings for RAG functionality';
COMMENT ON COLUMN document_chunks.content IS 'The text content of the document chunk';
COMMENT ON COLUMN document_chunks.embedding IS 'Vector embedding of the content for similarity search';
COMMENT ON COLUMN document_chunks.metadata IS 'Additional metadata about the document chunk (filename, page, etc.)';
COMMENT ON COLUMN document_chunks.conversation_id IS 'Links document chunks to specific conversations';
COMMENT ON FUNCTION match_document_chunks IS 'Function to find similar document chunks based on vector similarity within a specific conversation';
COMMENT ON FUNCTION get_conversation_stats IS 'Function to get statistics for a specific conversation';

-- Create a default conversation if none exist (optional)
INSERT INTO conversations (title) 
SELECT 'Default Conversation' 
WHERE NOT EXISTS (SELECT 1 FROM conversations);