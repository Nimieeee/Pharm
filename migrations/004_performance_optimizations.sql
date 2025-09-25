-- Performance optimization migrations for vector search and indexing
-- This migration adds optimized functions and indexes for better performance

-- Create optimized vector search function with better indexing
CREATE OR REPLACE FUNCTION match_documents_optimized(
  user_id UUID,
  query_embedding VECTOR(384),
  match_threshold FLOAT DEFAULT 0.1,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  source TEXT,
  metadata JSONB,
  similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    d.id,
    d.content,
    d.source,
    d.metadata,
    (1 - (d.embedding <=> query_embedding)) AS similarity
  FROM documents d
  WHERE 
    d.user_id = match_documents_optimized.user_id
    AND (1 - (d.embedding <=> query_embedding)) > match_threshold
  ORDER BY d.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Create function to get user document count efficiently
CREATE OR REPLACE FUNCTION get_user_document_count(user_id UUID)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
  doc_count INT;
BEGIN
  SELECT COUNT(*) INTO doc_count
  FROM documents
  WHERE documents.user_id = get_user_document_count.user_id;
  
  RETURN COALESCE(doc_count, 0);
END;
$$;

-- Create function to get vector index statistics
CREATE OR REPLACE FUNCTION get_vector_index_stats()
RETURNS TABLE (
  index_name TEXT,
  total_vectors BIGINT,
  index_size_mb FLOAT,
  last_updated TIMESTAMP WITH TIME ZONE,
  avg_search_time_ms FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    'documents_embedding_idx'::TEXT as index_name,
    COUNT(*)::BIGINT as total_vectors,
    (pg_total_relation_size('documents_embedding_idx')::FLOAT / 1024 / 1024) as index_size_mb,
    NOW() as last_updated,
    0.0::FLOAT as avg_search_time_ms -- Placeholder for actual timing data
  FROM documents
  WHERE embedding IS NOT NULL;
END;
$$;

-- Create function to optimize vector indexes
CREATE OR REPLACE FUNCTION optimize_vector_indexes()
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
  result JSONB;
BEGIN
  -- Reindex the vector index for better performance
  REINDEX INDEX documents_embedding_idx;
  
  -- Update table statistics
  ANALYZE documents;
  
  result := jsonb_build_object(
    'reindexed', 'documents_embedding_idx',
    'analyzed', 'documents',
    'timestamp', NOW()
  );
  
  RETURN result;
END;
$$;

-- Create additional indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_documents_user_id_created_at 
ON documents(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_documents_source 
ON documents(source) WHERE source IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_messages_user_id_created_at 
ON messages(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_role_user_id 
ON messages(role, user_id) WHERE role IN ('user', 'assistant');

-- Create partial indexes for better performance on common queries
CREATE INDEX IF NOT EXISTS idx_documents_recent 
ON documents(user_id, created_at DESC) 
WHERE created_at > (NOW() - INTERVAL '30 days');

CREATE INDEX IF NOT EXISTS idx_messages_recent 
ON messages(user_id, created_at DESC) 
WHERE created_at > (NOW() - INTERVAL '7 days');

-- Create function for efficient message pagination
CREATE OR REPLACE FUNCTION get_user_messages_paginated(
  user_id UUID,
  page_size INT DEFAULT 20,
  page_offset INT DEFAULT 0
)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  role TEXT,
  content TEXT,
  model_used TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  metadata JSONB,
  total_count BIGINT
)
LANGUAGE plpgsql
AS $$
DECLARE
  total_messages BIGINT;
BEGIN
  -- Get total count first
  SELECT COUNT(*) INTO total_messages
  FROM messages m
  WHERE m.user_id = get_user_messages_paginated.user_id;
  
  -- Return paginated results with total count
  RETURN QUERY
  SELECT
    m.id,
    m.user_id,
    m.role,
    m.content,
    m.model_used,
    m.created_at,
    m.metadata,
    total_messages
  FROM messages m
  WHERE m.user_id = get_user_messages_paginated.user_id
  ORDER BY m.created_at DESC
  LIMIT page_size
  OFFSET page_offset;
END;
$$;

-- Create function for efficient conversation history retrieval
CREATE OR REPLACE FUNCTION get_recent_conversation(
  user_id UUID,
  message_limit INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  role TEXT,
  content TEXT,
  model_used TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  metadata JSONB
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    m.id,
    m.user_id,
    m.role,
    m.content,
    m.model_used,
    m.created_at,
    m.metadata
  FROM messages m
  WHERE m.user_id = get_recent_conversation.user_id
  ORDER BY m.created_at ASC  -- Chronological order for conversation
  LIMIT message_limit;
END;
$$;

-- Create function for message statistics
CREATE OR REPLACE FUNCTION get_user_message_statistics(user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
  stats JSONB;
  total_messages INT;
  user_messages INT;
  assistant_messages INT;
  recent_messages INT;
  model_stats JSONB;
  first_message_date TIMESTAMP WITH TIME ZONE;
  last_message_date TIMESTAMP WITH TIME ZONE;
BEGIN
  -- Get basic counts
  SELECT COUNT(*) INTO total_messages
  FROM messages
  WHERE messages.user_id = get_user_message_statistics.user_id;
  
  SELECT COUNT(*) INTO user_messages
  FROM messages
  WHERE messages.user_id = get_user_message_statistics.user_id
    AND role = 'user';
  
  SELECT COUNT(*) INTO assistant_messages
  FROM messages
  WHERE messages.user_id = get_user_message_statistics.user_id
    AND role = 'assistant';
  
  SELECT COUNT(*) INTO recent_messages
  FROM messages
  WHERE messages.user_id = get_user_message_statistics.user_id
    AND created_at > (NOW() - INTERVAL '24 hours');
  
  -- Get model usage statistics
  SELECT jsonb_object_agg(model_used, count)
  INTO model_stats
  FROM (
    SELECT 
      COALESCE(model_used, 'unknown') as model_used,
      COUNT(*) as count
    FROM messages
    WHERE messages.user_id = get_user_message_statistics.user_id
      AND role = 'assistant'
    GROUP BY model_used
  ) model_counts;
  
  -- Get first and last message dates
  SELECT MIN(created_at), MAX(created_at)
  INTO first_message_date, last_message_date
  FROM messages
  WHERE messages.user_id = get_user_message_statistics.user_id;
  
  -- Build result JSON
  stats := jsonb_build_object(
    'total_messages', total_messages,
    'user_messages', user_messages,
    'assistant_messages', assistant_messages,
    'recent_messages', recent_messages,
    'models_used', COALESCE(model_stats, '{}'::jsonb),
    'first_message_date', first_message_date,
    'last_message_date', last_message_date,
    'avg_messages_per_day', 
      CASE 
        WHEN first_message_date IS NOT NULL AND last_message_date IS NOT NULL THEN
          total_messages::FLOAT / GREATEST(1, EXTRACT(DAYS FROM (last_message_date - first_message_date)) + 1)
        ELSE 0
      END
  );
  
  RETURN stats;
END;
$$;

-- Create function for bulk document operations
CREATE OR REPLACE FUNCTION bulk_insert_documents(
  documents JSONB
)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
  inserted_count INT := 0;
  doc JSONB;
BEGIN
  FOR doc IN SELECT * FROM jsonb_array_elements(documents)
  LOOP
    INSERT INTO documents (user_id, content, source, metadata, embedding)
    VALUES (
      (doc->>'user_id')::UUID,
      doc->>'content',
      doc->>'source',
      COALESCE(doc->'metadata', '{}'::jsonb),
      (doc->>'embedding')::VECTOR(384)
    );
    inserted_count := inserted_count + 1;
  END LOOP;
  
  RETURN inserted_count;
END;
$$;

-- Create materialized view for user statistics (for better performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS user_message_stats AS
SELECT 
  user_id,
  COUNT(*) as total_messages,
  COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
  COUNT(CASE WHEN role = 'assistant' THEN 1 END) as assistant_messages,
  COUNT(CASE WHEN created_at > (NOW() - INTERVAL '24 hours') THEN 1 END) as recent_messages,
  MIN(created_at) as first_message_date,
  MAX(created_at) as last_message_date,
  COUNT(DISTINCT DATE(created_at)) as active_days
FROM messages
GROUP BY user_id;

-- Create unique index on the materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_message_stats_user_id 
ON user_message_stats(user_id);

-- Create function to refresh user statistics
CREATE OR REPLACE FUNCTION refresh_user_message_stats()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY user_message_stats;
END;
$$;

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION match_documents_optimized(UUID, VECTOR, FLOAT, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_document_count(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_vector_index_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION optimize_vector_indexes() TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_messages_paginated(UUID, INT, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_recent_conversation(UUID, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_message_statistics(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION bulk_insert_documents(JSONB) TO authenticated;
GRANT EXECUTE ON FUNCTION refresh_user_message_stats() TO authenticated;

GRANT SELECT ON user_message_stats TO authenticated;

-- Add comments for documentation
COMMENT ON FUNCTION match_documents_optimized IS 'Optimized vector similarity search with better indexing';
COMMENT ON FUNCTION get_user_document_count IS 'Efficiently get document count for a user';
COMMENT ON FUNCTION get_vector_index_stats IS 'Get statistics about vector indexes';
COMMENT ON FUNCTION optimize_vector_indexes IS 'Optimize vector indexes for better performance';
COMMENT ON FUNCTION get_user_messages_paginated IS 'Get paginated messages for a user';
COMMENT ON FUNCTION get_recent_conversation IS 'Get recent conversation history in chronological order';
COMMENT ON FUNCTION get_user_message_statistics IS 'Get comprehensive message statistics for a user';
COMMENT ON FUNCTION bulk_insert_documents IS 'Bulk insert documents for better performance';
COMMENT ON MATERIALIZED VIEW user_message_stats IS 'Materialized view for user message statistics';