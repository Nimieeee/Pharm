-- Unlimited History Performance Optimizations
-- Database functions and indexes for efficient unlimited conversation history display

-- Create function to get all user messages without pagination limits (optimized)
CREATE OR REPLACE FUNCTION get_all_user_messages_unlimited(user_id UUID)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  role TEXT,
  content TEXT,
  model_used TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  metadata JSONB,
  conversation_id UUID
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
    m.metadata,
    m.conversation_id
  FROM messages m
  WHERE m.user_id = get_all_user_messages_unlimited.user_id
  ORDER BY m.created_at ASC;  -- Chronological order for conversation display
END;
$$;

-- Create function to get all conversation messages without pagination limits (optimized)
CREATE OR REPLACE FUNCTION get_conversation_messages_unlimited(
  user_id UUID,
  conversation_id UUID
)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  role TEXT,
  content TEXT,
  model_used TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  metadata JSONB,
  conversation_id UUID
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
    m.metadata,
    m.conversation_id
  FROM messages m
  WHERE m.user_id = get_conversation_messages_unlimited.user_id
    AND m.conversation_id = get_conversation_messages_unlimited.conversation_id
  ORDER BY m.created_at ASC;  -- Chronological order for conversation display
END;
$$;

-- Create function for chunked message loading (for virtual scrolling)
CREATE OR REPLACE FUNCTION get_messages_chunk(
  user_id UUID,
  conversation_id UUID DEFAULT NULL,
  chunk_offset INT DEFAULT 0,
  chunk_size INT DEFAULT 50
)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  role TEXT,
  content TEXT,
  model_used TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  metadata JSONB,
  conversation_id UUID,
  total_count BIGINT,
  chunk_index INT
)
LANGUAGE plpgsql
AS $$
DECLARE
  total_messages BIGINT;
BEGIN
  -- Get total count first
  IF conversation_id IS NOT NULL THEN
    SELECT COUNT(*) INTO total_messages
    FROM messages m
    WHERE m.user_id = get_messages_chunk.user_id
      AND m.conversation_id = get_messages_chunk.conversation_id;
  ELSE
    SELECT COUNT(*) INTO total_messages
    FROM messages m
    WHERE m.user_id = get_messages_chunk.user_id;
  END IF;
  
  -- Return chunked results with metadata
  RETURN QUERY
  SELECT
    m.id,
    m.user_id,
    m.role,
    m.content,
    m.model_used,
    m.created_at,
    m.metadata,
    m.conversation_id,
    total_messages,
    (ROW_NUMBER() OVER (ORDER BY m.created_at ASC) - 1)::INT as chunk_index
  FROM messages m
  WHERE m.user_id = get_messages_chunk.user_id
    AND (get_messages_chunk.conversation_id IS NULL OR m.conversation_id = get_messages_chunk.conversation_id)
  ORDER BY m.created_at ASC
  LIMIT chunk_size
  OFFSET chunk_offset;
END;
$$;

-- Create function to get message count efficiently (with caching support)
CREATE OR REPLACE FUNCTION get_message_count_optimized(
  user_id UUID,
  conversation_id UUID DEFAULT NULL
)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
  message_count INT;
BEGIN
  IF conversation_id IS NOT NULL THEN
    SELECT COUNT(*) INTO message_count
    FROM messages
    WHERE messages.user_id = get_message_count_optimized.user_id
      AND messages.conversation_id = get_message_count_optimized.conversation_id;
  ELSE
    SELECT COUNT(*) INTO message_count
    FROM messages
    WHERE messages.user_id = get_message_count_optimized.user_id;
  END IF;
  
  RETURN COALESCE(message_count, 0);
END;
$$;

-- Create function for efficient message range queries (for virtual scrolling)
CREATE OR REPLACE FUNCTION get_messages_range(
  user_id UUID,
  conversation_id UUID DEFAULT NULL,
  start_index INT DEFAULT 0,
  end_index INT DEFAULT 50
)
RETURNS TABLE (
  id UUID,
  user_id UUID,
  role TEXT,
  content TEXT,
  model_used TEXT,
  created_at TIMESTAMP WITH TIME ZONE,
  metadata JSONB,
  conversation_id UUID,
  row_index BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  WITH numbered_messages AS (
    SELECT
      m.id,
      m.user_id,
      m.role,
      m.content,
      m.model_used,
      m.created_at,
      m.metadata,
      m.conversation_id,
      ROW_NUMBER() OVER (ORDER BY m.created_at ASC) as row_num
    FROM messages m
    WHERE m.user_id = get_messages_range.user_id
      AND (get_messages_range.conversation_id IS NULL OR m.conversation_id = get_messages_range.conversation_id)
  )
  SELECT
    nm.id,
    nm.user_id,
    nm.role,
    nm.content,
    nm.model_used,
    nm.created_at,
    nm.metadata,
    nm.conversation_id,
    nm.row_num
  FROM numbered_messages nm
  WHERE nm.row_num > start_index AND nm.row_num <= end_index
  ORDER BY nm.created_at ASC;
END;
$$;

-- Create function for bulk message operations (for performance testing)
CREATE OR REPLACE FUNCTION create_test_messages(
  user_id UUID,
  conversation_id UUID,
  message_count INT DEFAULT 1000
)
RETURNS INT
LANGUAGE plpgsql
AS $$
DECLARE
  i INT;
  inserted_count INT := 0;
BEGIN
  FOR i IN 1..message_count LOOP
    INSERT INTO messages (user_id, conversation_id, role, content, model_used, metadata)
    VALUES (
      user_id,
      conversation_id,
      CASE WHEN i % 2 = 1 THEN 'user' ELSE 'assistant' END,
      'Test message #' || i || ' - This is a sample message for performance testing with unlimited history display.',
      CASE WHEN i % 2 = 0 THEN 'gemma2-9b-it' ELSE NULL END,
      jsonb_build_object('test_message', true, 'message_number', i)
    );
    inserted_count := inserted_count + 1;
    
    -- Commit in batches for better performance
    IF i % 100 = 0 THEN
      COMMIT;
    END IF;
  END LOOP;
  
  RETURN inserted_count;
END;
$$;

-- Create function to analyze message distribution for optimization
CREATE OR REPLACE FUNCTION analyze_message_distribution(user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
  result JSONB;
  total_messages INT;
  conversations_count INT;
  avg_messages_per_conversation FLOAT;
  largest_conversation_size INT;
  oldest_message_date TIMESTAMP WITH TIME ZONE;
  newest_message_date TIMESTAMP WITH TIME ZONE;
  date_range_days INT;
BEGIN
  -- Get basic statistics
  SELECT COUNT(*) INTO total_messages
  FROM messages
  WHERE messages.user_id = analyze_message_distribution.user_id;
  
  SELECT COUNT(DISTINCT conversation_id) INTO conversations_count
  FROM messages
  WHERE messages.user_id = analyze_message_distribution.user_id
    AND conversation_id IS NOT NULL;
  
  -- Calculate average messages per conversation
  IF conversations_count > 0 THEN
    avg_messages_per_conversation := total_messages::FLOAT / conversations_count;
  ELSE
    avg_messages_per_conversation := 0;
  END IF;
  
  -- Find largest conversation
  SELECT MAX(conv_size) INTO largest_conversation_size
  FROM (
    SELECT COUNT(*) as conv_size
    FROM messages
    WHERE messages.user_id = analyze_message_distribution.user_id
      AND conversation_id IS NOT NULL
    GROUP BY conversation_id
  ) conv_sizes;
  
  -- Get date range
  SELECT MIN(created_at), MAX(created_at)
  INTO oldest_message_date, newest_message_date
  FROM messages
  WHERE messages.user_id = analyze_message_distribution.user_id;
  
  IF oldest_message_date IS NOT NULL AND newest_message_date IS NOT NULL THEN
    date_range_days := EXTRACT(DAYS FROM (newest_message_date - oldest_message_date));
  ELSE
    date_range_days := 0;
  END IF;
  
  -- Build result JSON
  result := jsonb_build_object(
    'user_id', user_id,
    'total_messages', total_messages,
    'conversations_count', conversations_count,
    'avg_messages_per_conversation', avg_messages_per_conversation,
    'largest_conversation_size', COALESCE(largest_conversation_size, 0),
    'oldest_message_date', oldest_message_date,
    'newest_message_date', newest_message_date,
    'date_range_days', date_range_days,
    'messages_per_day', 
      CASE 
        WHEN date_range_days > 0 THEN total_messages::FLOAT / date_range_days
        ELSE 0
      END,
    'analysis_timestamp', NOW()
  );
  
  RETURN result;
END;
$$;

-- Create additional indexes for unlimited history performance
CREATE INDEX IF NOT EXISTS idx_messages_user_created_unlimited 
ON messages(user_id, created_at ASC) 
INCLUDE (id, role, content, model_used, metadata, conversation_id);

CREATE INDEX IF NOT EXISTS idx_messages_conversation_created_unlimited 
ON messages(user_id, conversation_id, created_at ASC) 
INCLUDE (id, role, content, model_used, metadata);

-- Create partial indexes for recent messages (hot data)
CREATE INDEX IF NOT EXISTS idx_messages_recent_unlimited 
ON messages(user_id, created_at ASC) 
WHERE created_at > (NOW() - INTERVAL '7 days')
INCLUDE (id, role, content, model_used, metadata, conversation_id);

-- Create index for efficient counting
CREATE INDEX IF NOT EXISTS idx_messages_count_only 
ON messages(user_id, conversation_id) 
WHERE conversation_id IS NOT NULL;

-- Create index for chunked loading
CREATE INDEX IF NOT EXISTS idx_messages_chunked_loading 
ON messages(user_id, created_at ASC, id) 
INCLUDE (role, content, model_used, metadata, conversation_id);

-- Create materialized view for message statistics (for performance dashboard)
CREATE MATERIALIZED VIEW IF NOT EXISTS unlimited_history_stats AS
SELECT 
  user_id,
  COUNT(*) as total_messages,
  COUNT(DISTINCT conversation_id) as total_conversations,
  MIN(created_at) as first_message_date,
  MAX(created_at) as last_message_date,
  MAX(created_at) - MIN(created_at) as date_range,
  COUNT(*) / GREATEST(1, EXTRACT(DAYS FROM (MAX(created_at) - MIN(created_at))) + 1) as avg_messages_per_day,
  MAX(conv_size.size) as largest_conversation_size,
  AVG(conv_size.size) as avg_conversation_size,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY conv_size.size) as median_conversation_size
FROM messages m
LEFT JOIN (
  SELECT 
    user_id,
    conversation_id,
    COUNT(*) as size
  FROM messages
  WHERE conversation_id IS NOT NULL
  GROUP BY user_id, conversation_id
) conv_size ON m.user_id = conv_size.user_id
GROUP BY m.user_id;

-- Create unique index on the materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_unlimited_history_stats_user_id 
ON unlimited_history_stats(user_id);

-- Create function to refresh unlimited history statistics
CREATE OR REPLACE FUNCTION refresh_unlimited_history_stats()
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY unlimited_history_stats;
END;
$$;

-- Create function to get performance recommendations
CREATE OR REPLACE FUNCTION get_unlimited_history_performance_recommendations(user_id UUID)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
  stats JSONB;
  recommendations JSONB := '[]'::JSONB;
  total_messages INT;
  largest_conversation INT;
  conversations_count INT;
BEGIN
  -- Get user statistics
  stats := analyze_message_distribution(user_id);
  total_messages := (stats->>'total_messages')::INT;
  largest_conversation := (stats->>'largest_conversation_size')::INT;
  conversations_count := (stats->>'conversations_count')::INT;
  
  -- Generate recommendations based on data size
  IF total_messages > 10000 THEN
    recommendations := recommendations || jsonb_build_array(
      jsonb_build_object(
        'type', 'performance',
        'priority', 'high',
        'message', 'Consider using virtual scrolling for conversations with ' || total_messages || ' messages',
        'action', 'enable_virtual_scrolling'
      )
    );
  END IF;
  
  IF largest_conversation > 1000 THEN
    recommendations := recommendations || jsonb_build_array(
      jsonb_build_object(
        'type', 'performance',
        'priority', 'medium',
        'message', 'Largest conversation has ' || largest_conversation || ' messages. Consider chunked loading.',
        'action', 'enable_chunked_loading'
      )
    );
  END IF;
  
  IF conversations_count > 50 THEN
    recommendations := recommendations || jsonb_build_array(
      jsonb_build_object(
        'type', 'organization',
        'priority', 'low',
        'message', 'You have ' || conversations_count || ' conversations. Consider archiving old ones.',
        'action', 'archive_old_conversations'
      )
    );
  END IF;
  
  IF total_messages < 100 THEN
    recommendations := recommendations || jsonb_build_array(
      jsonb_build_object(
        'type', 'optimization',
        'priority', 'low',
        'message', 'Small message count (' || total_messages || '). Standard loading is optimal.',
        'action', 'use_standard_loading'
      )
    );
  END IF;
  
  RETURN jsonb_build_object(
    'user_id', user_id,
    'statistics', stats,
    'recommendations', recommendations,
    'generated_at', NOW()
  );
END;
$$;

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION get_all_user_messages_unlimited(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_conversation_messages_unlimited(UUID, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_messages_chunk(UUID, UUID, INT, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_message_count_optimized(UUID, UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION get_messages_range(UUID, UUID, INT, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION create_test_messages(UUID, UUID, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION analyze_message_distribution(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION refresh_unlimited_history_stats() TO authenticated;
GRANT EXECUTE ON FUNCTION get_unlimited_history_performance_recommendations(UUID) TO authenticated;

GRANT SELECT ON unlimited_history_stats TO authenticated;

-- Add comments for documentation
COMMENT ON FUNCTION get_all_user_messages_unlimited IS 'Get all user messages without pagination for unlimited history display';
COMMENT ON FUNCTION get_conversation_messages_unlimited IS 'Get all conversation messages without pagination for unlimited history display';
COMMENT ON FUNCTION get_messages_chunk IS 'Get messages in chunks for virtual scrolling and lazy loading';
COMMENT ON FUNCTION get_message_count_optimized IS 'Get message count efficiently with optional conversation filtering';
COMMENT ON FUNCTION get_messages_range IS 'Get messages in a specific range for virtual scrolling';
COMMENT ON FUNCTION create_test_messages IS 'Create test messages for performance testing (development only)';
COMMENT ON FUNCTION analyze_message_distribution IS 'Analyze message distribution for performance optimization';
COMMENT ON FUNCTION get_unlimited_history_performance_recommendations IS 'Get performance recommendations based on user data';
COMMENT ON MATERIALIZED VIEW unlimited_history_stats IS 'Materialized view for unlimited history performance statistics';

-- Create trigger to automatically refresh stats (optional, for real-time stats)
CREATE OR REPLACE FUNCTION trigger_refresh_unlimited_history_stats()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  -- Refresh stats asynchronously (in a real implementation, you might use a job queue)
  -- For now, we'll just log that a refresh is needed
  PERFORM pg_notify('refresh_unlimited_history_stats', NEW.user_id::TEXT);
  RETURN NEW;
END;
$$;

-- Create trigger on messages table (optional - can be resource intensive)
-- Uncomment if you want real-time stats updates
-- CREATE TRIGGER trigger_messages_stats_refresh
--   AFTER INSERT OR UPDATE OR DELETE ON messages
--   FOR EACH ROW
--   EXECUTE FUNCTION trigger_refresh_unlimited_history_stats();