# Document Processing Speed Optimization

## Current Bottlenecks

1. **Mistral API Rate Limiting**: 1.1 seconds between embedding calls
2. **Sequential Processing**: Chunks processed one at a time
3. **Chunk Size**: 3000 characters per chunk

## Speed Optimization Options

### Option 1: Increase Chunk Size (Easiest - FREE)
**Current**: 3000 characters per chunk
**Recommended**: 6000-8000 characters per chunk

**Impact**: 
- Reduces number of API calls by 50-60%
- Faster processing with same rate limits
- Example: 100-page PDF = ~50 chunks instead of ~100 chunks

**Implementation**:
```bash
# Set in Render environment variables:
LANGCHAIN_CHUNK_SIZE=6000
LANGCHAIN_CHUNK_OVERLAP=600
```

**Pros**: Free, immediate effect
**Cons**: Slightly less granular context retrieval

---

### Option 2: Upgrade Mistral API Plan (PAID)
**Free Tier**: 1 request/second
**Paid Tier**: Higher rate limits

**Cost**: Check https://mistral.ai/pricing
**Impact**: 5-10x faster processing

---

### Option 3: Switch to Faster Embedding Model (FREE/PAID)
**Current**: Mistral API (1 req/sec, 1024 dims)
**Alternatives**:

#### A. OpenAI Embeddings (PAID - Faster)
- Model: `text-embedding-3-small`
- Rate Limit: 3000 requests/minute
- Cost: $0.02 per 1M tokens
- Speed: 100x faster than Mistral free tier

#### B. Cohere Embeddings (FREE tier available)
- Model: `embed-english-v3.0`
- Free tier: 100 requests/minute
- Speed: 60x faster than Mistral

#### C. Local Embeddings (FREE - Requires more RAM)
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- No rate limits
- Requires: Render paid plan with more RAM
- Speed: Instant (no API calls)

---

### Option 4: Parallel Processing (Requires Code Changes)
Process multiple chunks simultaneously while respecting rate limits.

**Implementation complexity**: Medium
**Speed improvement**: 2-3x faster

---

## Recommended Quick Fix (FREE)

### Increase Chunk Size to 6000

1. Go to Render Dashboard
2. Find your `pharmgpt-backend` service
3. Go to "Environment" tab
4. Add/Update these variables:
   ```
   LANGCHAIN_CHUNK_SIZE=6000
   LANGCHAIN_CHUNK_OVERLAP=600
   ```
5. Save and redeploy

**Expected Result**:
- 100-page PDF: ~2 minutes → ~1 minute
- 50-page PDF: ~1 minute → ~30 seconds

---

## Best Long-Term Solution

**Combination Approach**:
1. Increase chunk size to 6000 (FREE)
2. Switch to OpenAI embeddings ($5-10/month for typical usage)
3. Result: Documents process in 5-10 seconds instead of minutes

**OpenAI Setup** (if you want to switch):
```bash
# Environment variables:
USE_MISTRAL_EMBEDDINGS=false
OPENAI_API_KEY=your_key_here
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

---

## Current Processing Times (Estimated)

| Document Size | Current Time | With 6000 Chunks | With OpenAI |
|--------------|--------------|------------------|-------------|
| 10 pages     | ~20 seconds  | ~10 seconds      | ~2 seconds  |
| 50 pages     | ~1.5 minutes | ~45 seconds      | ~5 seconds  |
| 100 pages    | ~3 minutes   | ~1.5 minutes     | ~10 seconds |
| 500 pages    | ~15 minutes  | ~7 minutes       | ~30 seconds |

---

## Implementation Priority

1. ✅ **Increase chunk size** (5 minutes, FREE, 2x faster)
2. Consider OpenAI if budget allows (10 minutes, ~$10/month, 10x faster)
3. Optimize parallel processing later if needed
