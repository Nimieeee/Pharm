# Mistral Embeddings Upgrade Guide

This guide explains how to upgrade your PharmGPT instance to use Mistral embeddings for better semantic search.

## What's Changing?

- **Embedding Model**: Upgrading from simple hash-based embeddings to Mistral's `mistral-embed` model
- **Embedding Dimensions**: 384 → 1024 dimensions
- **Search Quality**: Significantly improved semantic understanding and relevance

## Prerequisites

- Mistral API key configured in environment variables
- Access to Supabase SQL Editor or database connection
- Backup of existing data (optional, but recommended)

## Migration Steps

### Step 1: Check Current Status

Run the migration helper script:

```bash
cd backend
python scripts/apply_mistral_migration.py
```

This will show you what needs to be done.

### Step 2: Apply Database Migration

You have two options:

#### Option A: Supabase Dashboard (Recommended)

1. Go to your Supabase project SQL Editor
2. Open `backend/migrations/005_simple_mistral_upgrade.sql`
3. Copy the entire contents
4. Paste into SQL Editor and execute

#### Option B: Command Line

If you have direct database access:

```bash
psql <your-database-url> < backend/migrations/005_simple_mistral_upgrade.sql
```

### Step 3: Verify Migration

The migration will:
- ✅ Upgrade embedding column to 1024 dimensions
- ✅ Add `embedding_version` column for tracking
- ✅ Add `updated_at` timestamp
- ✅ Create optimized indexes (HNSW + IVFFlat)
- ✅ Update similarity search function
- ⚠️  Clear existing embeddings (marked for regeneration)

### Step 4: Restart Backend

Restart your backend server to load the updated RAG service:

```bash
# If running locally
cd backend
uvicorn main:app --reload

# If on Render
# Trigger a new deployment or restart the service
```

### Step 5: Regenerate Embeddings

Re-upload your documents through the chat interface. The system will automatically:
- Generate new Mistral embeddings
- Mark them with `embedding_version = 'mistral-v1'`
- Store them in the upgraded schema

## Verification

### Check Embedding Statistics

Run this SQL query in Supabase:

```sql
SELECT * FROM get_embedding_stats();
```

You should see:
- `total_chunks`: Total number of document chunks
- `with_embeddings`: Chunks with embeddings
- `needs_upgrade`: Chunks that need re-embedding (should be 0 after re-upload)
- `mistral_embeddings`: Chunks using Mistral embeddings

### Test Search Quality

1. Upload a document in the chat interface
2. Ask questions about the document
3. Verify that responses are more accurate and contextually relevant

## Rollback (If Needed)

If you need to rollback:

1. The old embeddings are cleared, so you'll need to restore from backup
2. Or simply re-upload documents with the old system

## Performance Notes

### Mistral Embeddings API

- **Model**: `mistral-embed`
- **Dimensions**: 1024
- **Rate Limits**: Check your Mistral API plan
- **Cost**: ~$0.10 per 1M tokens

### Fallback Behavior

If Mistral API is unavailable:
- System falls back to hash-based embeddings
- Search still works but with reduced quality
- Marked with `embedding_version = 'hash-v1'`

## Troubleshooting

### "Mistral API key not configured"

Set the environment variable:
```bash
export MISTRAL_API_KEY=your_api_key_here
```

### "Embedding dimension mismatch"

The migration clears old embeddings. Re-upload your documents.

### "No similar chunks found"

1. Verify documents were uploaded successfully
2. Check that embeddings were generated (not NULL)
3. Try lowering the similarity threshold (default: 0.5)

### "Rate limit exceeded"

Mistral API has rate limits. If uploading many documents:
- Upload in smaller batches
- Wait between uploads
- Consider upgrading your Mistral API plan

## Benefits

After upgrading to Mistral embeddings:

✅ **Better Semantic Understanding**: Understands context and meaning, not just keywords
✅ **Improved Relevance**: Returns more relevant document chunks
✅ **Pharmacology-Aware**: Better understanding of medical/pharmaceutical terminology
✅ **Multilingual Support**: Works across multiple languages
✅ **Production-Ready**: Battle-tested embedding model from Mistral AI

## Support

If you encounter issues:
1. Check the backend logs for error messages
2. Verify your Mistral API key is valid
3. Ensure the migration was applied successfully
4. Check Supabase logs for database errors

## Next Steps

Consider these enhancements:
- Implement embedding caching to reduce API calls
- Add batch processing for large document uploads
- Monitor embedding generation costs
- Implement hybrid search (keyword + semantic)
