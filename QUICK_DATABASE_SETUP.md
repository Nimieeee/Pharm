# Quick Database Setup Guide

## 🚀 Get Your App Running in 5 Minutes

Your Pharmacology Chat App is almost ready! You just need to set up the database tables in Supabase.

## Option 1: Copy & Paste SQL (Easiest)

1. **Go to your Supabase Dashboard**
   - Visit [supabase.com](https://supabase.com)
   - Open your project

2. **Open SQL Editor**
   - Click "SQL Editor" in the left sidebar
   - Click "New Query"

3. **Run These SQL Commands** (copy and paste each one):

### Step 1: Initial Schema
```sql
-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    preferences JSONB DEFAULT '{}',
    subscription_tier TEXT DEFAULT 'free'
);

-- Create messages table with user association
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    model_used TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create documents table with pgvector support
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(384),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);
```

### Step 2: Security Policies
```sql
-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

CREATE POLICY "Users can insert own profile" ON users
    FOR INSERT WITH CHECK (auth.uid()::text = id::text);

-- Messages policies
CREATE POLICY "Users can view own messages" ON messages
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own messages" ON messages
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own messages" ON messages
    FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own messages" ON messages
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Documents policies
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own documents" ON documents
    FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own documents" ON documents
    FOR DELETE USING (auth.uid()::text = user_id::text);
```

### Step 3: Vector Functions
```sql
-- Function to search similar documents
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.78,
    match_count int DEFAULT 10,
    filter_user_id uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    content text,
    source text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        documents.id,
        documents.content,
        documents.source,
        documents.metadata,
        1 - (documents.embedding <=> query_embedding) AS similarity
    FROM documents
    WHERE 
        (filter_user_id IS NULL OR documents.user_id = filter_user_id)
        AND 1 - (documents.embedding <=> query_embedding) > match_threshold
    ORDER BY documents.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get user message statistics
CREATE OR REPLACE FUNCTION get_user_message_stats(user_uuid uuid)
RETURNS TABLE (
    total_messages bigint,
    user_messages bigint,
    assistant_messages bigint,
    first_message_date timestamp with time zone,
    last_message_date timestamp with time zone
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) as total_messages,
        COUNT(*) FILTER (WHERE role = 'user') as user_messages,
        COUNT(*) FILTER (WHERE role = 'assistant') as assistant_messages,
        MIN(created_at) as first_message_date,
        MAX(created_at) as last_message_date
    FROM messages
    WHERE user_id = user_uuid;
END;
$$;
```

4. **Click "Run" after pasting each section**

5. **Refresh your app** - It should now work!

## Option 2: Enable Authentication (Important!)

1. **Go to Authentication > Settings**
2. **Enable Email authentication**
3. **Set your site URL** (your Streamlit app URL)
4. **Configure email templates** (optional)

## ✅ That's It!

Your database is now set up and your Pharmacology Chat App should be fully functional!

## 🔧 Troubleshooting

- **Still seeing errors?** Make sure all three SQL sections were run successfully
- **Authentication issues?** Check that auth is enabled in Supabase
- **Need help?** Check the full `DATABASE_SETUP.md` for detailed instructions

---

**Next Steps:**
- Test user registration
- Try sending a chat message
- Upload some documents
- Switch between themes
- Try both Fast and Premium models