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
AS $
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
$;

-- Create function to get user message count
CREATE OR REPLACE FUNCTION get_user_message_count(user_id UUID)
RETURNS INT
LANGUAGE SQL STABLE
AS $
    SELECT COUNT(*)::INT
    FROM messages
    WHERE messages.user_id = get_user_message_count.user_id;
$;

-- Create function to get user document count
CREATE OR REPLACE FUNCTION get_user_document_count(user_id UUID)
RETURNS INT
LANGUAGE SQL STABLE
AS $
    SELECT COUNT(*)::INT
    FROM documents
    WHERE documents.user_id = get_user_document_count.user_id;
$;

-- Create function to clean up old messages (optional utility)
CREATE OR REPLACE FUNCTION cleanup_old_messages(
    days_old INT DEFAULT 30,
    user_id UUID DEFAULT NULL
)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
    deleted_count INT;
BEGIN
    DELETE FROM messages
    WHERE created_at < NOW() - INTERVAL '1 day' * days_old
        AND (user_id IS NULL OR messages.user_id = cleanup_old_messages.user_id);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

-- Function to search similar documents (alternative implementation)
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.78,
    match_count int DEFAULT 10,
    filter_user_id uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    content text,
    source text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.content,
        documents.source,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) AS similarity
    FROM documents
    WHERE 
        (filter_user_id IS NULL OR documents.user_id = filter_user_id)
        AND 1 - (documents.embedding <=> query_embedding) > match_threshold
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get user message statistics
CREATE OR REPLACE FUNCTION get_user_message_stats(user_uuid uuid)
RETURNS TABLE (
    total_messages bigint,
    user_messages bigint,
    assistant_messages bigint,
    first_message_date timestamp with time zone,
    last_message_date timestamp with time zone
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_messages,
        COUNT(*) FILTER (WHERE role = 'user') as user_messages,
        COUNT(*) FILTER (WHERE role = 'assistant') as assistant_messages,
        MIN(created_at) as first_message_date,
        MAX(created_at) as last_message_date
    FROM messages
    WHERE user_id = user_uuid;
END;
$$;