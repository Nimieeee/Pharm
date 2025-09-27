# Simple Chatbot Database Setup

This document explains how to set up the Supabase database for the simple chatbot application.

## Prerequisites

1. A Supabase project with pgvector extension enabled
2. Supabase project URL and anon key

## Setup Steps

### 1. Environment Configuration

Create a `.env.simple_chatbot` file with your Supabase credentials:

```bash
# Copy the example file
cp .env.simple_chatbot.example .env.simple_chatbot

# Edit with your actual values
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
```

### 2. Database Schema Setup

Run the schema SQL in your Supabase SQL editor:

```bash
# View the schema SQL
python test_database_cli.py --schema
```

Copy the output and run it in your Supabase project's SQL editor.

### 3. Test Connection

Test your database setup:

```bash
# Load environment variables and test
source .env.simple_chatbot
python test_database_cli.py
```

## Database Structure

The simple chatbot uses a minimal database structure:

- **document_chunks**: Stores text chunks with vector embeddings
  - `id`: UUID primary key
  - `content`: Text content of the chunk
  - `embedding`: 1536-dimensional vector (OpenAI embedding size)
  - `metadata`: JSON metadata about the chunk
  - `created_at`: Timestamp

## Usage in Code

```python
from database import SimpleChatbotDB

# Initialize database
db = SimpleChatbotDB()

# Test connection
if db.test_connection():
    print("Database ready!")
    
    # Get chunk count
    count = db.get_chunk_count()
    
    # Search similar chunks
    results = db.search_similar_chunks(embedding_vector)
```

## Troubleshooting

### Common Issues

1. **"document_chunks table does not exist"**
   - Run the schema SQL in Supabase SQL editor
   - Make sure pgvector extension is enabled

2. **"Supabase credentials not found"**
   - Check your environment variables
   - Verify `.env.simple_chatbot` file exists and is loaded

3. **Connection timeout**
   - Check your Supabase project URL
   - Verify your anon key is correct
   - Check network connectivity

### Testing

Use the provided test scripts:

- `test_database_cli.py`: Command-line testing (no Streamlit)
- `test_simple_database.py`: Streamlit-compatible testing

## Files

- `database.py`: Main database class
- `simple_chatbot_schema.sql`: Database schema
- `test_database_cli.py`: CLI testing script
- `.env.simple_chatbot.example`: Environment template