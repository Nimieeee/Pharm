# 🚀 Quick Deployment Guide

## Step-by-Step Database Setup

### 1. Create Supabase Project
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Save your **Project URL** and **Anon Key**

### 2. Run Migrations in Order

**IMPORTANT**: Run these SQL scripts in Supabase SQL Editor in this exact order:

#### Step 2.1: Fix Conflicts (Run First)
```sql
-- Migration 000: Fix function conflicts
DROP FUNCTION IF EXISTS match_document_chunks(VECTOR(384), FLOAT, INT);
DROP FUNCTION IF EXISTS match_document_chunks(VECTOR(384), UUID, UUID, FLOAT, INT);
DROP FUNCTION IF EXISTS match_document_chunks_langchain(VECTOR(384), FLOAT, INT, JSONB);
DROP FUNCTION IF EXISTS similarity_search_with_score(VECTOR(384), INT, JSONB);
DROP FUNCTION IF EXISTS get_conversation_stats(UUID, UUID);
DROP FUNCTION IF EXISTS get_embedding_stats();
DROP INDEX IF EXISTS document_chunks_embedding_idx;
DROP INDEX IF EXISTS document_chunks_embedding_hnsw_idx;
DROP INDEX IF EXISTS document_chunks_embedding_ivf_idx;
DROP VIEW IF EXISTS langchain_documents;
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Step 2.2: Create Base Schema
```sql
-- Create base tables if they don't exist
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding VECTOR(384),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Step 2.3: Add User Management
Copy and paste the entire content from `backend/migrations/001_add_users_and_support.sql`

#### Step 2.4: Create Admin User  
Copy and paste the entire content from `backend/migrations/002_create_admin_user.sql`

#### Step 2.5: Optimize for LangChain
Copy and paste the entire content from `backend/migrations/003_optimize_for_langchain.sql`

### 3. Set Admin Password
```sql
-- Update admin password (replace with actual bcrypt hash)
UPDATE users 
SET password_hash = '$2b$12$LQv3c1yqBwlVHpPjrcy.Oe3ZJBe/1cLN4B8B8B8B8B8B8B8B8B8B8'
WHERE email = 'admin@pharmgpt.com';
```

## Backend Deployment (Render)

### 1. Create Web Service
- Repository: Your GitHub repo
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python main.py`

### 2. Environment Variables
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SECRET_KEY=your_32_char_jwt_secret
MISTRAL_API_KEY=your_mistral_api_key
ADMIN_EMAIL=admin@pharmgpt.com
ADMIN_PASSWORD=your_secure_password
DEBUG=false
PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,https://your-app.netlify.app
```

## Frontend Deployment (Netlify)

### 1. Create Site
- Repository: Your GitHub repo
- Base Directory: `frontend`
- Build Command: `npm run build`
- Publish Directory: `frontend/dist`

### 2. Environment Variables
```bash
VITE_API_URL=https://your-render-app.onrender.com/api/v1
VITE_APP_NAME=PharmGPT
VITE_APP_VERSION=2.0.0
```

## Testing

1. Visit your Netlify URL
2. Register a new user
3. Login and test basic functionality
4. Login as admin with admin credentials

## Troubleshooting

### Function Conflict Error
If you get "function name is not unique" error:
1. Run the conflict fix SQL first (Step 2.1)
2. Then run other migrations in order

### CORS Error
Update `ALLOWED_ORIGINS` in Render with your actual Netlify URL

### Database Connection Error
- Check Supabase credentials
- Ensure project is not paused
- Verify pgvector extension is enabled

## Quick Links
- **Supabase**: [supabase.com](https://supabase.com)
- **Render**: [render.com](https://render.com)
- **Netlify**: [netlify.com](https://netlify.com)
- **Mistral AI**: [console.mistral.ai](https://console.mistral.ai)

---

**Need help?** Check the full `DEPLOYMENT.md` for detailed instructions.