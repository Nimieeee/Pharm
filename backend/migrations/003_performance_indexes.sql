-- ============================================
-- PharmGPT Database Performance Indexes
-- Run this in your Supabase SQL Editor
-- ============================================

-- 1. Accelerate fetching messages for a specific conversation
-- This makes loading conversation history instant
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
ON messages(conversation_id);

-- 2. Accelerate fetching messages with ordering
CREATE INDEX IF NOT EXISTS idx_messages_conversation_created 
ON messages(conversation_id, created_at);

-- 3. Accelerate the sidebar list (loading past conversations for a user)
CREATE INDEX IF NOT EXISTS idx_conversations_user_updated 
ON conversations(user_id, updated_at DESC);

-- 4. Accelerate document chunk lookups
CREATE INDEX IF NOT EXISTS idx_document_chunks_conversation 
ON document_chunks(conversation_id);

-- 5. (VITAL for RAG) Make vector search fast with HNSW index
-- HNSW is faster than IVFFlat for similarity search
-- Uncomment the appropriate line based on your pgvector version:

-- For pgvector 0.5.0+:
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw 
-- ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- For older pgvector (IVFFlat fallback):
-- CREATE INDEX IF NOT EXISTS idx_chunks_embedding_ivfflat 
-- ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- 6. Index for user email lookups (auth performance)
CREATE INDEX IF NOT EXISTS idx_users_email 
ON users(email);

-- ============================================
-- Verify indexes were created
-- ============================================
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename IN ('messages', 'conversations', 'document_chunks', 'users');
