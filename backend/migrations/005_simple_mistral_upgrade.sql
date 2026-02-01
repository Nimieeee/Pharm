-- Simple migration to upgrade to Mistral embeddings (1024 dimensions)
-- This is a simpler approach that modifies the existing table

-- Step 1: Add embedding_version column if it doesn't exist
ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS embedding_version VARCHAR(50) DEFAULT 'hash-v1';

-- Step 2: Add updated_at column if it doesn't exist
ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Step 3: Create or replace the update trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Step 4: Create trigger for updated_at
DROP TRIGGER IF EXISTS update_document_chunks_updated_at ON document_chunks;
CREATE TRIGGER update_document_chunks_updated_at
    BEFORE UPDATE ON document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Step 5: Drop existing indexes on embedding column
DROP INDEX IF EXISTS document_chunks_embedding_hnsw_idx;
DROP INDEX IF EXISTS document_chunks_embedding_ivf_idx;

-- Step 6: Alter embedding column to support 1024 dimensions
-- Note: This will clear existing embeddings, but that's okay since we're upgrading
ALTER TABLE document_chunks 
ALTER COLUMN embedding TYPE VECTOR(1024);

-- Step 7: Create new indexes for 1024-dimensional embeddings
CREATE INDEX document_chunks_embedding_hnsw_idx 
ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX document_chunks_embedding_ivf_idx 
ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Step 8: Update existing records to mark them for re-embedding
UPDATE document_chunks 
SET embedding_version = 'needs-upgrade', 
    embedding = NULL,
    updated_at = NOW()
WHERE embedding_version = 'hash-v1' OR embedding_version IS NULL;

-- Step 9: Create updated similarity search function for 1024 dimensions
CREATE OR REPLACE FUNCTION match_documents_with_user_isolation(
    query_embedding VECTOR(1024),
    conversation_uuid UUID,
    user_session_uuid UUID,
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10
)
RETURNS TABLE(
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    created_at TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.content,
        document_chunks.metadata,
        1 - (document_chunks.embedding <=> query_embedding) AS similarity,
        document_chunks.created_at
    FROM document_chunks
    WHERE 
        document_chunks.conversation_id = conversation_uuid
        AND document_chunks.user_id = user_session_uuid
        AND document_chunks.embedding IS NOT NULL
        AND 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Step 10: Create function to get migration statistics
CREATE OR REPLACE FUNCTION get_embedding_stats()
RETURNS TABLE(
    total_chunks BIGINT,
    with_embeddings BIGINT,
    needs_upgrade BIGINT,
    mistral_embeddings BIGINT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_chunks,
        COUNT(*) FILTER (WHERE embedding IS NOT NULL) as with_embeddings,
        COUNT(*) FILTER (WHERE embedding_version = 'needs-upgrade') as needs_upgrade,
        COUNT(*) FILTER (WHERE embedding_version = 'mistral-v1') as mistral_embeddings
    FROM document_chunks;
END;
$$;

-- Add helpful comments
COMMENT ON COLUMN document_chunks.embedding_version IS 'Version of embedding model used (hash-v1, mistral-v1, etc)';
COMMENT ON COLUMN document_chunks.updated_at IS 'Timestamp of last update';
COMMENT ON FUNCTION match_documents_with_user_isolation IS 'Search similar documents using 1024-dimensional embeddings';
COMMENT ON FUNCTION get_embedding_stats IS 'Get statistics about embeddings in the database';

-- Print success message
DO $$
BEGIN
    RAISE NOTICE '✅ Migration completed successfully!';
    RAISE NOTICE '📊 Embedding dimension upgraded to 1024';
    RAISE NOTICE '💡 Existing embeddings have been cleared and marked for upgrade';
    RAISE NOTICE '📝 Re-upload documents to generate new Mistral embeddings';
END $$;
