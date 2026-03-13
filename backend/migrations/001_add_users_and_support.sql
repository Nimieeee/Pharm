-- Migration 001: Add users table and support requests table
-- This migration adds user management and support functionality to the existing schema

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_admin BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create support_requests table
CREATE TABLE IF NOT EXISTS support_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    admin_response TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add user_id column to existing conversations table
ALTER TABLE conversations 
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Add user_id column to existing messages table  
ALTER TABLE messages
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Add user_id column to existing document_chunks table
ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS users_email_idx ON users(email);
CREATE INDEX IF NOT EXISTS users_is_admin_idx ON users(is_admin);
CREATE INDEX IF NOT EXISTS users_is_active_idx ON users(is_active);
CREATE INDEX IF NOT EXISTS conversations_user_id_idx ON conversations(user_id);
CREATE INDEX IF NOT EXISTS messages_user_id_idx ON messages(user_id);
CREATE INDEX IF NOT EXISTS document_chunks_user_id_idx ON document_chunks(user_id);
CREATE INDEX IF NOT EXISTS support_requests_user_id_idx ON support_requests(user_id);
CREATE INDEX IF NOT EXISTS support_requests_status_idx ON support_requests(status);
CREATE INDEX IF NOT EXISTS support_requests_created_at_idx ON support_requests(created_at);

-- Update the match_document_chunks function to include user isolation
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding VECTOR(384),
    conversation_uuid UUID,
    user_session_uuid UUID,
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
    WHERE 
        document_chunks.conversation_id = conversation_uuid
        AND document_chunks.user_id = user_session_uuid
        AND 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create function to get conversation statistics with user isolation
CREATE OR REPLACE FUNCTION get_conversation_stats(
    conversation_uuid UUID,
    user_session_uuid UUID
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
         WHERE conversation_id = conversation_uuid AND user_id = user_session_uuid) as message_count,
        (SELECT COUNT(DISTINCT metadata->>'filename') FROM document_chunks 
         WHERE conversation_id = conversation_uuid AND user_id = user_session_uuid) as document_count,
        (SELECT MAX(created_at) FROM messages 
         WHERE conversation_id = conversation_uuid AND user_id = user_session_uuid) as last_activity;
END;
$$;

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_support_requests_updated_at BEFORE UPDATE ON support_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE users IS 'User accounts with authentication and authorization';
COMMENT ON TABLE support_requests IS 'User support requests and admin responses';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password';
COMMENT ON COLUMN users.is_admin IS 'Admin access flag for administrative functions';
COMMENT ON COLUMN conversations.user_id IS 'User who owns this conversation';
COMMENT ON COLUMN messages.user_id IS 'User who created this message';
COMMENT ON COLUMN document_chunks.user_id IS 'User who uploaded the document';
COMMENT ON FUNCTION match_document_chunks IS 'Find similar document chunks with user and conversation isolation';
COMMENT ON FUNCTION get_conversation_stats IS 'Get conversation statistics with user isolation';