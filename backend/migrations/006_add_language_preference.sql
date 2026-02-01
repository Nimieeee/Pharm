-- Add language column to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';

-- Comment on column
COMMENT ON COLUMN users.language IS 'User preferred language for AI responses and interface';
