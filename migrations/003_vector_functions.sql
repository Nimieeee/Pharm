-- Create function for user-scoped vector similarity search
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(384),
    match_threshold FLOAT,
    match_count INT,
    user_id UUID
)
RETURNS TABLE(
    id UUID,
    content TEXT,
    source TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT
        documents.id,
        documents.content,
        documents.source,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) AS similarity
    FROM documents
    WHERE documents.user_id = match_documents.user_id
        AND 1 - (documents.embedding <=> query_embedding) > match_threshold
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Create function to get user message count
CREATE OR REPLACE FUNCTION get_user_message_count(user_id UUID)
RETURNS INT
LANGUAGE SQL STABLE
AS $$
    SELECT COUNT(*)::INT
    FROM messages
    WHERE messages.user_id = get_user_message_count.user_id;
$$;

-- Create function to get user document count
CREATE OR REPLACE FUNCTION get_user_document_count(user_id UUID)
RETURNS INT
LANGUAGE SQL STABLE
AS $$
    SELECT COUNT(*)::INT
    FROM documents
    WHERE documents.user_id = get_user_document_count.user_id;
$$;

-- Create function to clean up old messages (optional utility)
CREATE OR REPLACE FUNCTION cleanup_old_messages(
    days_old INT DEFAULT 30,
    user_id UUID DEFAULT NULL
)
RETURNS INT
LANGUAGE SQL
AS $$
    DELETE FROM messages
    WHERE created_at < NOW() - INTERVAL '1 day' * days_old
        AND (cleanup_old_messages.user_id IS NULL OR messages.user_id = cleanup_old_messages.user_id);
    
    SELECT ROW_COUNT()::INT;
$$;