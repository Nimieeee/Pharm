# Database Setup Guide

This guide explains how to set up the database schema for the Pharmacology Chat App with user data isolation and pgvector support.

## Prerequisites

1. Supabase project with pgvector extension enabled
2. Environment variables configured:
   - `SUPABASE_URL`: Your Supabase project URL
   - `SUPABASE_SERVICE_KEY`: Your Supabase service role key (for admin operations)

## Setup Methods

### Method 1: Using Supabase SQL Editor (Recommended)

1. Open your Supabase project dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of `complete_schema.sql`
4. Run the script

This will create:
- All required tables (users, messages, documents)
- Indexes for performance optimization
- Row Level Security (RLS) policies for user data isolation
- pgvector extension and vector indexes
- Utility functions for vector similarity search

### Method 2: Using Python Migration Runner

1. Install required dependencies:
   ```bash
   pip install supabase
   ```

2. Set environment variables:
   ```bash
   export SUPABASE_URL="your_supabase_url"
   export SUPABASE_SERVICE_KEY="your_service_key"
   ```

3. Run migrations:
   ```bash
   python run_migrations.py
   ```

## Database Schema

### Tables Created

#### users
- `id`: UUID primary key
- `email`: Unique user email
- `created_at`: Timestamp
- `preferences`: JSONB for user preferences
- `subscription_tier`: Text field for subscription level

#### messages
- `id`: UUID primary key
- `user_id`: Foreign key to users table
- `role`: 'user' or 'assistant'
- `content`: Message content
- `model_used`: AI model used for response
- `created_at`: Timestamp
- `metadata`: JSONB for additional data

#### documents
- `id`: UUID primary key
- `user_id`: Foreign key to users table
- `content`: Document text content
- `source`: Document source/filename
- `metadata`: JSONB for additional data
- `embedding`: Vector(384) for semantic search
- `created_at`: Timestamp

### Row Level Security (RLS)

All tables have RLS enabled with policies ensuring:
- Users can only access their own data
- No cross-user data leakage
- Secure multi-tenant architecture

### Vector Search Functions

#### match_documents()
Performs user-scoped similarity search on documents using pgvector:
```sql
SELECT * FROM match_documents(
    query_embedding := '[0.1, 0.2, ...]'::vector,
    match_threshold := 0.7,
    match_count := 5,
    user_id := 'user-uuid'
);
```

## Usage with Python

The `database_utils.py` file provides a `DatabaseUtils` class with methods for:

- User profile management
- Message storage and retrieval
- Document management with vector search
- User-scoped queries with automatic isolation

Example usage:
```python
from database_utils import DatabaseUtils
from supabase import create_client

# Initialize
client = create_client(url, key)
db_utils = DatabaseUtils(client)

# Save a message
message = db_utils.save_message(
    user_id="user-uuid",
    role="user",
    content="What is pharmacokinetics?"
)

# Perform similarity search
results = db_utils.similarity_search(
    user_id="user-uuid",
    query_embedding=[0.1, 0.2, ...],
    limit=5
)
```

## Security Features

1. **Row Level Security**: Automatic user data isolation at the database level
2. **User-scoped functions**: All database functions respect user boundaries
3. **Cascade deletion**: User data is automatically cleaned up when user is deleted
4. **Vector search isolation**: Similarity search only operates on user's own documents

## Performance Optimizations

1. **Indexes**: Created on frequently queried columns (user_id, created_at)
2. **Vector index**: IVFFlat index for fast similarity search
3. **Query optimization**: Functions designed for efficient user-scoped queries

## Verification

After setup, verify the schema is working:

1. Check tables exist:
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```

2. Verify RLS is enabled:
   ```sql
   SELECT tablename, rowsecurity FROM pg_tables 
   WHERE schemaname = 'public';
   ```

3. Test vector extension:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```