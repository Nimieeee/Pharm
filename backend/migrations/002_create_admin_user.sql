-- Migration 002: Create default admin user and associate existing data
-- This migration creates the default admin user and associates existing conversations with them

-- Insert default admin user (password will be hashed by the application)
-- Note: This is a placeholder - the actual admin user should be created via the API
INSERT INTO users (id, email, password_hash, first_name, last_name, is_admin, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001'::UUID,
    'admin@pharmgpt.com',
    '$2b$12$placeholder_hash_will_be_replaced_by_app',
    'Admin',
    'User',
    TRUE,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Associate existing conversations with the admin user (if any exist without user_id)
UPDATE conversations 
SET user_id = '00000000-0000-0000-0000-000000000001'::UUID
WHERE user_id IS NULL;

-- Associate existing messages with the admin user (if any exist without user_id)
UPDATE messages 
SET user_id = '00000000-0000-0000-0000-000000000001'::UUID
WHERE user_id IS NULL;

-- Associate existing document chunks with the admin user (if any exist without user_id)
UPDATE document_chunks 
SET user_id = '00000000-0000-0000-0000-000000000001'::UUID
WHERE user_id IS NULL;

-- Make user_id columns NOT NULL after data migration
ALTER TABLE conversations ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE messages ALTER COLUMN user_id SET NOT NULL;
ALTER TABLE document_chunks ALTER COLUMN user_id SET NOT NULL;

-- Add check to ensure admin user exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE is_admin = TRUE) THEN
        RAISE EXCEPTION 'No admin user found after migration. Please create an admin user.';
    END IF;
END $$;