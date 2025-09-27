-- Schema update for multi-conversation support
-- Run this after the main schema to add conversation support

-- Update the match_document_chunks function to support conversation filtering
DROP FUNCTION IF EXISTS match_document_chunks(VECTOR(384), FLOAT, INT);

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

COMMENT ON FUNCTION match_document_chunks IS 'Function to find similar document chunks based on vector similarity within a specific conversation';
COMMENT ON FUNCTION get_conversation_stats IS 'Function to get statistics for a specific conversation';