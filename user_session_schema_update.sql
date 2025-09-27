-- User Session Privacy Schema Update
-- Run this to add user session isolation for privacy

-- Add user_session_id to conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS user_session_id TEXT DEFAULT 'anonymous';

-- Add user_session_id to messages table  
ALTER TABLE messages
ADD COLUMN IF NOT EXISTS user_session_id TEXT DEFAULT 'anonymous';

-- Add user_session_id to document_chunks table
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS user_session_id TEXT DEFAULT 'anonymous';

-- Create indexes for user session filtering
CREATE INDEX IF NOT EXISTS conversations_user_session_idx ON conversations(user_session_id);
CREATE INDEX IF NOT EXISTS messages_user_session_idx ON messages(user_session_id);
CREATE INDEX IF NOT EXISTS document_chunks_user_session_idx ON document_chunks(user_session_id);

-- Update the match_document_chunks function to include user session filtering
DROP FUNCTION IF EXISTS match_document_chunks(VECTOR(384), UUID, FLOAT, INT);

CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding VECTOR(384),
    conversation_uuid UUID,
    user_session_uuid TEXT,
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
    AND document_chunks.user_session_id = user_session_uuid
    AND 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Update the get_conversation_stats function to include user session filtering
DROP FUNCTION IF EXISTS get_conversation_stats(UUID);

CREATE OR REPLACE FUNCTION get_conversation_stats(
    conversation_uuid UUID,
    user_session_uuid TEXT
)
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
        (SELECT COUNT(*) FROM messages 
         WHERE conversation_id = conversation_uuid 
         AND user_session_id = user_session_uuid) as message_count,
        (SELECT COUNT(DISTINCT metadata->>'filename') FROM document_chunks 
         WHERE conversation_id = conversation_uuid 
         AND user_session_id = user_session_uuid) as document_count,
        (SELECT GREATEST(
            COALESCE(MAX(created_at), '1970-01-01'::timestamptz) 
        ) FROM (
            SELECT created_at FROM messages 
            WHERE conversation_id = conversation_uuid 
            AND user_session_id = user_session_uuid
            UNION ALL
            SELECT created_at FROM document_chunks 
            WHERE conversation_id = conversation_uuid 
            AND user_session_id = user_session_uuid
        ) as activities) as last_activity;
END;
$$;

COMMENT ON FUNCTION match_document_chunks IS 'Function to find similar document chunks based on vector similarity within a specific conversation and user session';
COMMENT ON FUNCTION get_conversation_stats IS 'Function to get statistics for a specific conversation and user session';

-- Add comments for new columns
COMMENT ON COLUMN conversations.user_session_id IS 'Unique session ID for user privacy isolation';
COMMENT ON COLUMN messages.user_session_id IS 'Unique session ID for user privacy isolation';
COMMENT ON COLUMN document_chunks.user_session_id IS 'Unique session ID for user privacy isolation';