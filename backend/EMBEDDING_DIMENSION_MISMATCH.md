# Embedding Dimension Mismatch Issue

## Problem

Your database is configured for **384-dimensional** embeddings, but the system is trying to store **1024-dimensional** embeddings (Mistral's embedding size).

### Error Message
```
'expected 384 dimensions, not 1024'
```

## Why This Happened

Your Supabase database was originally set up for a different embedding model (probably sentence-transformers or similar) that uses 384 dimensions. Mistral's `mistral-embed` model uses 1024 dimensions.

## Solutions

### Option 1: Update Database to 1024 Dimensions (Recommended)

This allows you to use Mistral embeddings properly.

**Steps:**

1. Go to your Supabase SQL Editor
2. Run the migration SQL from `backend/migrations/006_update_embedding_dimensions.sql`
3. This will:
   - Drop the existing embedding column
   - Create a new 1024-dimensional embedding column
   - Update the similarity search function
   - **Delete all existing embeddings** (you'll need to re-upload documents)

**To apply:**
```bash
cd backend
python scripts/update_embedding_dimensions.py
```

This will display the SQL you need to run in Supabase.

### Option 2: Use 384-Dimensional Fallback (Quick Fix)

Temporarily change the fallback to generate 384 dimensions to match your current database.

**Edit `backend/app/core/config.py`:**
```python
# Change from:
MISTRAL_EMBED_DIMENSIONS: int = 1024

# To:
MISTRAL_EMBED_DIMENSIONS: int = 384
```

**Pros:**
- Works immediately
- No database changes needed
- Existing embeddings still work

**Cons:**
- Hash-based embeddings (not semantic)
- Can't use real Mistral embeddings
- Less accurate similarity search

### Option 3: Wait for Mistral API Rate Limit to Reset

If you just want to test with real Mistral embeddings:
- Wait 1-2 hours for rate limit to reset
- Upload ONE small document
- See if it works with real Mistral embeddings

## Recommended Approach

1. **For Production**: Use Option 1 - Update database to 1024 dimensions
2. **For Quick Testing**: Use Option 2 - Change config to 384 dimensions
3. **For Patience**: Use Option 3 - Wait for rate limit reset

## After Fixing

Once you've chosen a solution:

1. **If you updated database (Option 1)**:
   - Re-upload all your documents
   - They'll use proper Mistral embeddings (when not rate-limited)
   - Better similarity search

2. **If you changed config (Option 2)**:
   - System will work with 384-dim hash embeddings
   - Upload documents normally
   - Less accurate but functional

## Current Status

- ✅ PDF processing: Working (38 chunks created)
- ✅ Text splitting: Working
- ❌ Embedding storage: Failing (dimension mismatch)
- ⚠️ Mistral API: Rate limited (429 errors)

## Next Steps

Choose one of the options above and apply it. I recommend Option 1 for the best long-term solution.
