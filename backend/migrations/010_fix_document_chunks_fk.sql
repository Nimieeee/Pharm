-- Fix Foreign Key on document_chunks to allow cascading deletes
-- This ensures that when a conversation is deleted, its document chunks are also deleted
-- preventing "violates foreign key constraint" errors.

DO $$
DECLARE
    constraint_name text;
BEGIN
    -- Find the foreign key constraint on document_chunks referencing conversations
    SELECT tc.constraint_name INTO constraint_name
    FROM information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY' 
      AND tc.table_name = 'document_chunks'
      AND kcu.column_name = 'conversation_id'
      AND ccu.table_name = 'conversations';

    -- If found, drop it
    IF constraint_name IS NOT NULL THEN
        EXECUTE 'ALTER TABLE document_chunks DROP CONSTRAINT ' || quote_ident(constraint_name);
    END IF;
END $$;

-- Re-add the constraint with ON DELETE CASCADE
ALTER TABLE document_chunks
ADD CONSTRAINT document_chunks_conversation_id_fkey
FOREIGN KEY (conversation_id)
REFERENCES conversations(id)
ON DELETE CASCADE;

-- Also ensure user_id has cascade (it was added in 001 but good to verify)
DO $$
DECLARE
    constraint_name text;
BEGIN
    SELECT tc.constraint_name INTO constraint_name
    FROM information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY' 
      AND tc.table_name = 'document_chunks'
      AND kcu.column_name = 'user_id';

    IF constraint_name IS NOT NULL THEN
        -- We assume if it exists it's fine, but to be safe we could recreate it.
        -- For now let's just focus on conversation_id which is the critical one for this error.
        NULL;
    END IF;
END $$;

-- Enable RLS on document_chunks if not enabled
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Add RLS policies for document_chunks
DROP POLICY IF EXISTS "Users can view their own document chunks" ON document_chunks;
DROP POLICY IF EXISTS "Users can insert their own document chunks" ON document_chunks;
DROP POLICY IF EXISTS "Users can delete their own document chunks" ON document_chunks;

CREATE POLICY "Users can view their own document chunks"
    ON document_chunks FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own document chunks"
    ON document_chunks FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own document chunks"
    ON document_chunks FOR DELETE
    USING (auth.uid() = user_id);
