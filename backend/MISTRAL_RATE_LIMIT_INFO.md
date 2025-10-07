# Mistral API Rate Limiting

## Current Issue

You're hitting Mistral API rate limits when uploading documents:

```
❌ Mistral API error: 429 - Service tier capacity exceeded for this model
⚠️  Using fallback hash-based embedding
```

## What's Happening

1. **Document Upload**: When you upload a PDF, it's split into chunks (e.g., 38 chunks)
2. **Embedding Generation**: Each chunk needs an embedding (1024-dimensional vector)
3. **Rate Limit Hit**: Mistral's free tier has limited requests per minute
4. **Fallback Activated**: System uses hash-based embeddings instead

## Impact

### With Hash Embeddings (Current Fallback)
- ✅ Documents are stored successfully
- ✅ You can ask questions
- ⚠️ Similarity search is less accurate (hash-based, not semantic)
- ⚠️ AI might not find the most relevant chunks

### With Mistral Embeddings (Ideal)
- ✅ Semantic similarity search
- ✅ Better document retrieval
- ✅ More accurate AI responses
- ❌ Requires staying within rate limits

## Solutions

### Option 1: Wait Between Uploads (Free)
- Upload one document at a time
- Wait 1-2 minutes between uploads
- Allows rate limit to reset

### Option 2: Upgrade Mistral Plan (Paid)
- Get higher rate limits
- Process multiple documents quickly
- Better for production use

### Option 3: Use Alternative Embedding Service
- OpenAI embeddings (text-embedding-3-small)
- Cohere embeddings
- Self-hosted models (sentence-transformers)

## Current Behavior

The system is working correctly with fallback embeddings:
- ✅ PDF processing: Working (38 chunks created)
- ✅ Chunk storage: Working (with hash embeddings)
- ✅ Similarity search: Working (less accurate)
- ✅ AI responses: Working (may miss some context)

## Recommendation

For testing/development:
- Use the current setup with hash embeddings
- Upload documents one at a time
- Wait between uploads if you hit rate limits

For production:
- Upgrade to Mistral paid tier
- Or switch to a different embedding provider
- Consider caching embeddings to reduce API calls

## Checking Your Rate Limit

Mistral free tier typically allows:
- ~60 requests per minute
- ~1000 requests per day

A single document with 38 chunks = 38 embedding requests
If you upload multiple documents quickly, you'll hit the limit.
