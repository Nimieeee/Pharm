# Conversation Management Migration Instructions

This document provides instructions for manually running the conversation management migration.

## Overview

The conversation management feature requires adding a new `conversations` table and updating the existing `messages` table to support multiple conversation threads per user.

## Manual Migration Steps

### Step 1: Access Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to the **SQL Editor** section
3. Create a new query

### Step 2: Run the Migration SQL

Copy and paste the following SQL into the SQL Editor and execute it:

```sql
-- Migration 006: Add conversation management support
-- This migration adds conversation management functionality

-- Create conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'New Conversation',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true
);

-- Add conversation_id to existing messages table
ALTER TABLE messages ADD COLUMN IF NOT EXISTS conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE;

-- Create indexes for efficient conversation-based queries
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_active ON conversations(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);

-- Enable Row Level Security on conversations table
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- Conversations table RLS policies
-- Users can only access their own conversations
CREATE POLICY "Users can view own conversations" ON conversations
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own conversations" ON conversations
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own conversations" ON conversations
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own conversations" ON conversations
    FOR DELETE USING (auth.uid() = user_id);

-- Function to update conversation updated_at timestamp
CREATE OR REPLACE FUNCTION update_conversation_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversations 
    SET updated_at = NOW(), 
        message_count = (
            SELECT COUNT(*) 
            FROM messages 
            WHERE conversation_id = NEW.conversation_id
        )
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update conversation timestamp when messages are added
CREATE TRIGGER update_conversation_on_message_insert
    AFTER INSERT ON messages
    FOR EACH ROW
    WHEN (NEW.conversation_id IS NOT NULL)
    EXECUTE FUNCTION update_conversation_timestamp();

-- Function to create default conversation for existing users
CREATE OR REPLACE FUNCTION create_default_conversations()
RETURNS void AS $$
DECLARE
    user_record RECORD;
    default_conversation_id UUID;
BEGIN
    -- For each user who has messages but no conversations
    FOR user_record IN 
        SELECT DISTINCT u.id as user_id
        FROM users u
        WHERE EXISTS (
            SELECT 1 FROM messages m WHERE m.user_id = u.id AND m.conversation_id IS NULL
        )
    LOOP
        -- Create a default conversation
        INSERT INTO conversations (user_id, title, created_at)
        VALUES (user_record.user_id, 'Default Conversation', NOW())
        RETURNING id INTO default_conversation_id;
        
        -- Update all messages without conversation_id to use the default conversation
        UPDATE messages 
        SET conversation_id = default_conversation_id
        WHERE user_id = user_record.user_id AND conversation_id IS NULL;
        
        -- Update message count for the conversation
        UPDATE conversations 
        SET message_count = (
            SELECT COUNT(*) 
            FROM messages 
            WHERE conversation_id = default_conversation_id
        )
        WHERE id = default_conversation_id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Execute the function to create default conversations for existing users
SELECT create_default_conversations();

-- Function to get user conversations with message counts
CREATE OR REPLACE FUNCTION get_user_conversations(user_id UUID)
RETURNS TABLE(
    id UUID,
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    message_count INTEGER,
    is_active BOOLEAN,
    last_message_preview TEXT
)
LANGUAGE SQL STABLE
AS $$
    SELECT 
        c.id,
        c.title,
        c.created_at,
        c.updated_at,
        c.message_count,
        c.is_active,
        COALESCE(
            (SELECT content 
             FROM messages m 
             WHERE m.conversation_id = c.id 
             ORDER BY m.created_at DESC 
             LIMIT 1), 
            'No messages yet'
        ) as last_message_preview
    FROM conversations c
    WHERE c.user_id = get_user_conversations.user_id
        AND c.is_active = true
    ORDER BY c.updated_at DESC;
$$;
```

### Step 3: Verify Migration

After running the SQL, verify that the migration was successful:

1. Check that the `conversations` table was created:
   ```sql
   SELECT * FROM conversations LIMIT 5;
   ```

2. Check that the `messages` table has the new `conversation_id` column:
   ```sql
   SELECT id, user_id, conversation_id, role, content 
   FROM messages 
   LIMIT 5;
   ```

3. Test the conversation function:
   ```sql
   SELECT * FROM get_user_conversations('your-user-id-here');
   ```

### Step 4: Restart Application

After successfully running the migration:

1. Restart your Streamlit application
2. The conversation tabs should now be available in the chat interface
3. Existing messages should be automatically assigned to a "Default Conversation"

## Troubleshooting

### If you get RLS (Row Level Security) errors:

If you encounter Row Level Security policy errors, you may need to temporarily disable RLS on the tables:

```sql
-- Temporarily disable RLS (not recommended for production)
ALTER TABLE conversations DISABLE ROW LEVEL SECURITY;
ALTER TABLE messages DISABLE ROW LEVEL SECURITY;
```

### If the migration partially fails:

You can run individual parts of the migration. The most important parts are:

1. Creating the conversations table
2. Adding the conversation_id column to messages
3. Creating the get_user_conversations function

### If you need to rollback:

To rollback the migration (remove conversation management):

```sql
-- Remove conversation_id column from messages
ALTER TABLE messages DROP COLUMN IF EXISTS conversation_id;

-- Drop conversations table
DROP TABLE IF EXISTS conversations CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_conversation_timestamp();
DROP FUNCTION IF EXISTS create_default_conversations();
DROP FUNCTION IF EXISTS get_user_conversations(UUID);
```

## Features Enabled

After successful migration, you will have:

- ✅ Conversation tabs in the chat interface
- ✅ Ability to create new conversations
- ✅ Conversation switching
- ✅ Automatic conversation title generation
- ✅ Conversation management (rename, delete)
- ✅ Isolated message history per conversation
- ✅ Unlimited message history display per conversation

## Support

If you encounter issues with the migration, please check:

1. That you have admin access to your Supabase project
2. That all required tables (users, messages) exist
3. That your Supabase project has sufficient permissions for DDL operations

For additional help, refer to the Supabase documentation or create an issue in the project repository.