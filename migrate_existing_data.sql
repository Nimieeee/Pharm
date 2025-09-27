-- Migration script for existing document_chunks data
-- Run this AFTER the main schema setup if you have existing document chunks without conversation_id

-- Create a default conversation for existing data
INSERT INTO conversations (id, title) 
VALUES ('00000000-0000-0000-0000-000000000001', 'Migrated Data')
ON CONFLICT (id) DO NOTHING;

-- Update existing document_chunks to use the default conversation
UPDATE document_chunks 
SET conversation_id = '00000000-0000-0000-0000-000000000001'
WHERE conversation_id IS NULL;

-- Make conversation_id NOT NULL after migration
ALTER TABLE document_chunks 
ALTER COLUMN conversation_id SET NOT NULL;