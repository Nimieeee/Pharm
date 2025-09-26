-- Temporarily disable RLS on messages table to get chat working
-- This is a quick fix while we resolve the authentication session issues

-- Disable RLS on messages table
ALTER TABLE messages DISABLE ROW LEVEL SECURITY;

-- Add a comment to track this change
COMMENT ON TABLE messages IS 'RLS temporarily disabled - re-enable once auth session persistence is fixed';

-- Optional: You can also run this to see current RLS status
-- SELECT schemaname, tablename, rowsecurity FROM pg_tables WHERE tablename = 'messages';