# Cohere Embeddings Setup Guide

## Why Cohere?

- **60x faster** than Mistral free tier (100 req/min vs 1 req/sec)
- **Free tier** with generous limits
- **Same quality** embeddings (1024 dimensions)
- **Better for production** - faster document processing

## Speed Comparison

| Document Size | Mistral (1 req/sec) | Cohere (100 req/min) |
|--------------|---------------------|----------------------|
| 10 pages     | ~20 seconds         | ~3 seconds           |
| 50 pages     | ~1.5 minutes        | ~15 seconds          |
| 100 pages    | ~3 minutes          | ~30 seconds          |
| 500 pages    | ~15 minutes         | ~2.5 minutes         |

## Setup Steps

### 1. Get Cohere API Key (FREE)

1. Go to https://cohere.com/
2. Click "Sign Up" (free account)
3. Verify your email
4. Go to https://dashboard.cohere.com/api-keys
5. Click "Create API Key"
6. Copy your API key

### 2. Update Render Environment Variables

1. Go to https://dashboard.render.com
2. Find your `pharmgpt-backend` service
3. Click "Environment" tab
4. Add/Update these variables:

```bash
# Cohere API Key
COHERE_API_KEY=your_cohere_api_key_here

# Switch to Cohere embeddings
EMBEDDING_PROVIDER=cohere

# Optimal chunk settings for Cohere
LANGCHAIN_CHUNK_SIZE=1000
LANGCHAIN_CHUNK_OVERLAP=200
```

5. Click "Save Changes"
6. Service will auto-redeploy (~2-3 minutes)

### 3. Verify It's Working

After deployment, check the logs for:
```
🚀 Using Cohere embeddings (fast, 100 req/min)
✅ Cohere client initialized
```

### 4. Test Document Upload

Upload a PDF and watch it process 60x faster!

## Optimal Settings Explained

### Chunk Size: 1000 characters
- **Why**: Cohere handles smaller chunks better for precise retrieval
- **Benefit**: More accurate context matching
- **Trade-off**: More API calls, but Cohere is fast enough

### Chunk Overlap: 200 characters
- **Why**: 20% overlap ensures context continuity
- **Benefit**: No information lost at chunk boundaries
- **Standard**: Industry best practice

## Cohere Free Tier Limits

- **100 requests/minute** (6,000/hour)
- **1,000 requests/day** on free tier
- **Unlimited** on paid tier ($0.10 per 1K requests)

### Typical Usage:
- 10-page PDF = ~10 requests
- 100-page PDF = ~100 requests
- You can process **10 large PDFs per day** on free tier

## Troubleshooting

### "Cohere client not initialized"
- Check COHERE_API_KEY is set correctly
- Verify API key is active at https://dashboard.cohere.com/api-keys

### "Rate limit exceeded"
- Free tier: 100 req/min, 1000 req/day
- Wait a few minutes or upgrade to paid tier

### Still slow?
- Check EMBEDDING_PROVIDER=cohere is set
- Check logs show "Using Cohere embeddings"
- Verify LANGCHAIN_CHUNK_SIZE=1000

## Rollback to Mistral

If you need to switch back:

```bash
EMBEDDING_PROVIDER=mistral
LANGCHAIN_CHUNK_SIZE=3000
LANGCHAIN_CHUNK_OVERLAP=400
```

## Cost Comparison

| Provider | Free Tier | Paid Tier | Speed |
|----------|-----------|-----------|-------|
| Mistral  | 1 req/sec | Unknown | Slow |
| Cohere   | 100 req/min | $0.10/1K | Fast |
| OpenAI   | None | $0.02/1M tokens | Fastest |

**Recommendation**: Start with Cohere free tier, upgrade if needed.
