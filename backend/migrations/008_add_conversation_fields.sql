-- Add is_pinned and is_archived columns to conversations table

ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE;
ALTER TABLE conversations ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE;

-- Add index for faster filtering
CREATE INDEX IF NOT EXISTS idx_conversations_pinned ON conversations(is_pinned);
CREATE INDEX IF NOT EXISTS idx_conversations_archived ON conversations(is_archived);
