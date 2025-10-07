# Mistral Embeddings - Quick Start

## What Changed?

Your PharmGPT now uses **Mistral AI embeddings** for document search instead of simple hash-based embeddings. This means:

✅ **Much better semantic understanding** of your documents
✅ **More accurate context retrieval** when answering questions
✅ **Better handling of medical/pharmaceutical terminology**

## How to Enable

### 1. Apply Database Migration

Go to your Supabase SQL Editor and run:

```bash
backend/migrations/005_simple_mistral_upgrade.sql
```

**Or** use the helper script:

```bash
cd backend
python scripts/apply_mistral_migration.py
```

This will show you the exact steps.

### 2. Verify Mistral API Key

Make sure your `.env` file has:

```bash
MISTRAL_API_KEY=your_mistral_api_key_here
```

### 3. Restart Backend

```bash
# Render will auto-restart on deployment
# Or locally:
cd backend
uvicorn main:app --reload
```

### 4. Re-upload Documents

- Go to your chat interface
- Upload your documents again
- They'll automatically get Mistral embeddings

## How It Works

**Before (Hash-based):**
```
Document → Simple Hash → 384D Vector → Basic Search
```

**After (Mistral):**
```
Document → Mistral API → 1024D Vector → Semantic Search
```

## Testing

1. Upload a pharmaceutical document
2. Ask: "What are the drug interactions?"
3. Notice more relevant and accurate responses!

## Fallback

If Mistral API is unavailable:
- System automatically falls back to hash-based embeddings
- Search still works (just not as good)
- No errors or crashes

## Cost

Mistral embeddings cost approximately:
- **$0.10 per 1M tokens**
- A typical PDF page ≈ 500 tokens
- 1000 pages ≈ $0.05

Very affordable for the quality improvement!

## Need Help?

See the full guide: `backend/MISTRAL_EMBEDDINGS_UPGRADE.md`
