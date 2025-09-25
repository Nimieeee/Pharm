-- Temporary RLS bypass for testing chat functionality
-- This should be reverted once proper authentication is working

-- Temporarily disable RLS on messages table to allow testing
ALTER TABLE messages DISABLE ROW LEVEL SECURITY;

-- Add a comment to remind us this is temporary
COMMENT ON TABLE messages IS 'RLS temporarily disabled for testing - re-enable once auth is fixed';

-- Optional: Create a more permissive policy for testing
-- (Uncomment if you want to re-enable RLS with a permissive policy instead)
/*
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Drop existing restrictive policies
DROP POLICY IF EXISTS "Users can view own messages" ON messages;
DROP POLICY IF EXISTS "Users can insert own messages" ON messages;
DROP POLICY IF EXISTS "Users can update own messages" ON messages;
DROP POLICY IF EXISTS "Users can delete own messages" ON messages;

-- Create permissive policies for testing
CREATE POLICY "Allow all message operations for testing" ON messages
    FOR ALL USING (true) WITH CHECK (true);
*/