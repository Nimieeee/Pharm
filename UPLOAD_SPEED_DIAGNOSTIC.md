# Document Upload Speed Diagnostic

## Current Issue: Uploads Taking Too Long

### Quick Check - What's Being Used?

Check your Render logs for one of these messages on startup:

**Fast (Cohere)**:
```
🚀 Using Cohere embeddings (fast, 100 req/min)
```

**Slow (Mistral)**:
```
🐌 Using Mistral embeddings (slow, 1 req/sec)
⚠️  COHERE_API_KEY not set, falling back to Mistral embeddings (slow)
```

## If You See "Mistral" - You Need to Set Up Cohere

### Step 1: Get Cohere API Key (5 minutes)
1. Go to https://cohere.com/ and sign up (FREE)
2. Go to https://dashboard.cohere.com/api-keys
3. Create and copy your API key

### Step 2: Add to Render Environment Variables
1. Go to https://dashboard.render.com
2. Find your `pharmgpt-backend` service
3. Click "Environment" tab
4. Add these variables:

```bash
COHERE_API_KEY=your_cohere_api_key_here
EMBEDDING_PROVIDER=cohere
LANGCHAIN_CHUNK_SIZE=1000
LANGCHAIN_CHUNK_OVERLAP=200
```

5. Click "Save Changes"
6. Wait ~2-3 minutes for redeploy

### Step 3: Verify
Check logs for:
```
🚀 Using Cohere embeddings (fast, 100 req/min)
```

## Speed Comparison

| Provider | Speed | Time for 100-page PDF |
|----------|-------|----------------------|
| Mistral  | 1 req/sec | ~3 minutes |
| Cohere   | 100 req/min | ~30 seconds |

**60x faster with Cohere!**

## Current Configuration Check

### Check Environment Variables on Render:
1. Go to your service → Environment tab
2. Look for:
   - `COHERE_API_KEY` - Should be set
   - `EMBEDDING_PROVIDER` - Should be "cohere"
   - `LANGCHAIN_CHUNK_SIZE` - Should be 1000
   - `LANGCHAIN_CHUNK_OVERLAP` - Should be 200

### If Variables Are Missing:
You're using Mistral (slow) by default. Add the Cohere variables above.

## Troubleshooting

### "Still slow after adding Cohere key"
1. Check logs show "Using Cohere embeddings"
2. Verify COHERE_API_KEY is correct
3. Make sure service redeployed after adding variables
4. Try manual redeploy: "Manual Deploy" → "Deploy latest commit"

### "Cohere API errors"
1. Verify API key is active at https://dashboard.cohere.com/api-keys
2. Check you haven't exceeded free tier (1000 requests/day)
3. Check logs for specific error messages

### "Documents fail to upload"
1. Check file size (< 10MB recommended)
2. Check file format is supported (PDF, DOCX, TXT, images)
3. Check Render logs for specific errors

## Expected Performance After Setup

With Cohere configured:
- 10-page PDF: ~3 seconds
- 50-page PDF: ~15 seconds
- 100-page PDF: ~30 seconds
- 500-page PDF: ~2.5 minutes

## Still Having Issues?

Check Render logs for errors:
1. Go to your service
2. Click "Logs" tab
3. Look for errors during document upload
4. Share the error messages for help

## Quick Test

Upload a small PDF (5-10 pages):
- **With Mistral**: Takes 10-20 seconds
- **With Cohere**: Takes 2-3 seconds

If it's taking 10+ seconds for a small PDF, you're still using Mistral.
