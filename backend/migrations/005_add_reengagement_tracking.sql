-- Migration: Add reengagement_email_sent_at column to users table
-- This tracks when a re-engagement email was last sent to prevent duplicates

-- Add the column if it doesn't exist
ALTER TABLE users ADD COLUMN IF NOT EXISTS reengagement_email_sent_at TIMESTAMPTZ;

-- Add last_login column if it doesn't exist (should already be there)
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMPTZ;

-- Create an index for efficient querying of inactive users
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);
CREATE INDEX IF NOT EXISTS idx_users_reengagement ON users(reengagement_email_sent_at);

-- Optional: Set last_login to created_at for existing users who have never logged in
-- This prevents sending re-engagement emails to brand new users
UPDATE users SET last_login = created_at WHERE last_login IS NULL;
