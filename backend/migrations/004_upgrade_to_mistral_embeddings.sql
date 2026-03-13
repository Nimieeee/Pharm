-- Migration 004: Upgrade to Mistral embeddings (1024 dimensions)
-- This migration updates the database schema to support Mistral embeddings

-- Ensure pgvector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding_version column to track embedding model versions
ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS embedding_version VARCHAR(50) DEFAULT 'hash-v1';

-- Add updated_at column for tracking when embeddings were last updated
ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_document_chunks_updated_at ON document_chunks;
CREATE TRIGGER update_document_chunks_updated_at
    BEFORE UPDATE ON document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create backup table for existing embeddings
CREATE TABLE IF NOT EXISTS document_chunks_backup AS 
SELECT * FROM document_chunks WHERE 1=0;

-- Function to backup existing data before migration
CREATE OR REPLACE FUNCTION backup_existing_embeddings()
RETURNS INTEGER AS $$
DECLARE
    backup_count INTEGER;
BEGIN
    -- Clear existing backup
    DELETE FROM document_chunks_backup;
    
    -- Backup current data
    INSERT INTO document_chunks_backup 
    SELECT * FROM document_chunks;
    
    GET DIAGNOSTICS backup_count = ROW_COUNT;
    
    RAISE NOTICE 'Backed up % existing document chunks', backup_count;
    RETURN backup_count;
END;
$$ LANGUAGE plpgsql;

-- Create new table with 1024-dimensional embeddings
CREATE TABLE IF NOT EXISTS document_chunks_new (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024), -- Mistral embeddings are 1024 dimensions
    embedding_version VARCHAR(50) DEFAULT 'mistral-v1',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for the new table
CREATE INDEX IF NOT EXISTS document_chunks_new_conversation_id_idx 
ON document_chunks_new(conversation_id);

CREATE INDEX IF NOT EXISTS document_chunks_new_user_id_idx 
ON document_chunks_new(user_id);

CREATE INDEX IF NOT EXISTS document_chunks_new_embedding_version_idx 
ON document_chunks_new(embedding_version);

-- Create HNSW index for 1024-dimensional embeddings
CREATE INDEX IF NOT EXISTS document_chunks_new_embedding_hnsw_idx 
ON document_chunks_new USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Create IVFFlat index as fallback
CREATE INDEX IF NOT EXISTS document_chunks_new_embedding_ivf_idx 
ON document_chunks_new USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create metadata indexes
CREATE INDEX IF NOT EXISTS document_chunks_new_metadata_user_id_idx 
ON document_chunks_new USING GIN ((metadata->>'user_id'));

CREATE INDEX IF NOT EXISTS document_chunks_new_metadata_conversation_id_idx 
ON document_chunks_new USING GIN ((metadata->>'conversation_id'));

CREATE INDEX IF NOT EXISTS document_chunks_new_metadata_filename_idx 
ON document_chunks_new USING GIN ((metadata->>'filename'));

-- Function to migrate data from old table to new table
CREATE OR REPLACE FUNCTION migrate_to_new_embeddings()
RETURNS INTEGER AS $$
DECLARE
    migrated_count INTEGER := 0;
    chunk_record RECORD;
BEGIN
    -- Copy non-embedding data to new table (embeddings will be regenerated)
    FOR chunk_record IN 
        SELECT id, conversation_id, user_id, content, metadata, created_at
        FROM document_chunks
    LOOP
        INSERT INTO document_chunks_new (
            id, conversation_id, user_id, content, embedding, 
            embedding_version, metadata, created_at, updated_at
        ) VALUES (
            chunk_record.id,
            chunk_record.conversation_id,
            chunk_record.user_id,
            chunk_record.content,
            NULL, -- Embedding will be regenerated
            'pending-migration',
            chunk_record.metadata,
            chunk_record.created_at,
            NOW()
        );
        
        migrated_count := migrated_count + 1;
        
        -- Log progress every 100 records
        IF migrated_count % 100 = 0 THEN
            RAISE NOTICE 'Migrated % records...', migrated_count;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Migration completed: % records migrated', migrated_count;
    RETURN migrated_count;
END;
$$ LANGUAGE plpgsql;

-- Function to swap tables (use with caution)
CREATE OR REPLACE FUNCTION swap_to_new_embeddings_table()
RETURNS BOOLEAN AS $$
BEGIN
    -- This function should only be called after embeddings are regenerated
    -- and the new table is fully populated
    
    -- Rename current table to old
    ALTER TABLE document_chunks RENAME TO document_chunks_old;
    
    -- Rename new table to current
    ALTER TABLE document_chunks_new RENAME TO document_chunks;
    
    -- Update trigger
    DROP TRIGGER IF EXISTS update_document_chunks_updated_at ON document_chunks;
    CREATE TRIGGER update_document_chunks_updated_at
        BEFORE UPDATE ON document_chunks
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    
    RAISE NOTICE 'Table swap completed successfully';
    RETURN TRUE;
    
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Table swap failed: %', SQLERRM;
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function to rollback migration
CREATE OR REPLACE FUNCTION rollback_embeddings_migration()
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if old table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'document_chunks_old') THEN
        -- Drop current table
        DROP TABLE IF EXISTS document_chunks;
        
        -- Restore old table
        ALTER TABLE document_chunks_old RENAME TO document_chunks;
        
        -- Recreate trigger
        DROP TRIGGER IF EXISTS update_document_chunks_updated_at ON document_chunks;
        CREATE TRIGGER update_document_chunks_updated_at
            BEFORE UPDATE ON document_chunks
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        
        RAISE NOTICE 'Migration rollback completed successfully';
        RETURN TRUE;
    ELSE
        RAISE NOTICE 'No old table found - rollback not possible';
        RETURN FALSE;
    END IF;
    
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Rollback failed: %', SQLERRM;
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Updated similarity search function for 1024 dimensions
CREATE OR REPLACE FUNCTION match_documents_with_user_isolation_v2(
    query_embedding VECTOR(1024),
    conversation_uuid UUID,
    user_session_uuid UUID,
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE(
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT,
    created_at TIMESTAMP WITH TIME ZONE,
    embedding_version VARCHAR(50)
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
        document_chunks.created_at,
        document_chunks.embedding_version
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

-- Function to get embedding statistics
CREATE OR REPLACE FUNCTION get_embedding_migration_stats()
RETURNS TABLE(
    total_chunks BIGINT,
    old_embeddings BIGINT,
    new_embeddings BIGINT,
    pending_migration BIGINT,
    embedding_versions TEXT[]
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_chunks,
        COUNT(*) FILTER (WHERE embedding_version LIKE 'hash%' OR embedding_version = 'hash-v1') as old_embeddings,
        COUNT(*) FILTER (WHERE embedding_version LIKE 'mistral%') as new_embeddings,
        COUNT(*) FILTER (WHERE embedding_version = 'pending-migration') as pending_migration,
        ARRAY_AGG(DISTINCT embedding_version) as embedding_versions
    FROM document_chunks;
END;
$$;

-- Function to clean up migration artifacts
CREATE OR REPLACE FUNCTION cleanup_migration_artifacts()
RETURNS BOOLEAN AS $$
BEGIN
    -- Drop backup table if migration is successful
    DROP TABLE IF EXISTS document_chunks_backup;
    
    -- Drop old table if it exists and migration is complete
    DROP TABLE IF EXISTS document_chunks_old;
    
    -- Drop new table if it exists and wasn't swapped
    DROP TABLE IF EXISTS document_chunks_new;
    
    RAISE NOTICE 'Migration artifacts cleaned up successfully';
    RETURN TRUE;
    
EXCEPTION WHEN OTHERS THEN
    RAISE EXCEPTION 'Cleanup failed: %', SQLERRM;
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON FUNCTION backup_existing_embeddings() IS 'Backup existing embeddings before migration';
COMMENT ON FUNCTION migrate_to_new_embeddings() IS 'Migrate data structure for 1024-dimensional embeddings';
COMMENT ON FUNCTION swap_to_new_embeddings_table() IS 'Swap to new embeddings table after regeneration';
COMMENT ON FUNCTION rollback_embeddings_migration() IS 'Rollback migration to previous state';
COMMENT ON FUNCTION match_documents_with_user_isolation_v2 IS 'Updated similarity search for 1024-dimensional embeddings';
COMMENT ON FUNCTION get_embedding_migration_stats() IS 'Get statistics about embedding migration progress';
COMMENT ON FUNCTION cleanup_migration_artifacts() IS 'Clean up temporary migration tables and artifacts';

-- Create view for monitoring migration progress
CREATE OR REPLACE VIEW embedding_migration_progress AS
SELECT 
    total_chunks,
    old_embeddings,
    new_embeddings,
    pending_migration,
    CASE 
        WHEN total_chunks = 0 THEN 0
        ELSE ROUND((new_embeddings::FLOAT / total_chunks::FLOAT) * 100, 2)
    END as migration_percentage,
    embedding_versions
FROM get_embedding_migration_stats();

COMMENT ON VIEW embedding_migration_progress IS 'Monitor progress of embedding migration';

-- Instructions for manual migration process
/*
MIGRATION INSTRUCTIONS:

1. Backup existing data:
   SELECT backup_existing_embeddings();

2. Check current state:
   SELECT * FROM embedding_migration_progress;

3. Migrate data structure (this does NOT regenerate embeddings):
   SELECT migrate_to_new_embeddings();

4. At this point, use the application to regenerate embeddings for all chunks
   The application should detect chunks with embedding_version = 'pending-migration'
   and regenerate their embeddings using the Mistral API

5. After all embeddings are regenerated, swap tables:
   SELECT swap_to_new_embeddings_table();

6. Verify migration success:
   SELECT * FROM embedding_migration_progress;

7. Clean up (only after confirming migration success):
   SELECT cleanup_migration_artifacts();

ROLLBACK (if needed):
   SELECT rollback_embeddings_migration();

MONITORING:
   SELECT * FROM embedding_migration_progress;
   SELECT * FROM get_embedding_migration_stats();
*/