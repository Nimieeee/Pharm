# Rate Limit Handling

## Overview

PharmGPT now includes automatic retry logic with exponential backoff to handle Mistral API rate limits (429 errors) gracefully.

## Implementation

### AI Chat Responses

When generating AI responses, the system automatically retries on rate limit errors:

**Retry Strategy**:
- **Max retries**: 3 attempts
- **Backoff delays**: 2s, 5s, 10s (exponential)
- **Total max wait**: ~17 seconds

**User Experience**:
- No error shown to user during retries
- Loading spinner continues
- Success after retry
- Only shows error if all retries fail

### Document Embeddings

When processing uploaded documents, embeddings are generated with retry logic:

**Retry Strategy**:
- **Max retries**: 3 attempts
- **Backoff delays**: 1s, 3s, 5s
- **Fallback**: Hash-based embeddings if all retries fail

**User Experience**:
- Document upload continues
- Retries happen automatically
- Falls back to hash embeddings if needed
- Upload succeeds even with rate limits

## Error Messages

### Before (Without Retry)
```
❌ AI service error (429). Please try again.
```

### After (With Retry)
```
✅ Response generated successfully
(or after 3 failed retries)
❌ The AI service is currently experiencing high demand. Please try again in a moment.
```

## Technical Details

### AI Service (backend/app/services/ai.py)

```python
# Retry logic for rate limits (429 errors)
max_retries = 3
retry_delays = [2, 5, 10]  # Exponential backoff

for attempt in range(max_retries):
    try:
        response = await client.post(...)
        
        if response.status_code == 429:
            if attempt < max_retries - 1:
                delay = retry_delays[attempt]
                await asyncio.sleep(delay)
                continue
            else:
                return "High demand message"
    except httpx.TimeoutException:
        # Also retry on timeout
        ...
```

### RAG Service (backend/app/services/rag.py)

```python
# Retry logic for embedding generation
max_retries = 3
retry_delays = [1, 3, 5]

for attempt in range(max_retries):
    response = client.post(...)
    
    if response.status_code == 429:
        if attempt < max_retries - 1:
            time.sleep(retry_delays[attempt])
            continue
        else:
            # Fallback to hash-based embeddings
            return self._generate_fallback_embedding(text)
```

## Benefits

### For Users
- ✅ **Seamless experience** - No manual retries needed
- ✅ **Fewer errors** - Most rate limits handled automatically
- ✅ **Better UX** - Clear messages when retries fail
- ✅ **No data loss** - Documents still process with fallback

### For System
- ✅ **Resilient** - Handles API rate limits gracefully
- ✅ **Efficient** - Exponential backoff prevents hammering API
- ✅ **Fallback** - Hash embeddings when Mistral unavailable
- ✅ **Logging** - Clear logs for debugging

## Rate Limit Scenarios

### Scenario 1: Single Rate Limit Hit
1. User sends message
2. First attempt → 429 error
3. Wait 2 seconds
4. Second attempt → Success ✅
5. User sees response (total delay: ~2s)

### Scenario 2: Multiple Rate Limits
1. User uploads document
2. First chunk → 429 error
3. Wait 1 second, retry → 429 error
4. Wait 3 seconds, retry → Success ✅
5. Continue processing remaining chunks

### Scenario 3: Persistent Rate Limit
1. User sends message
2. All 3 attempts → 429 error
3. Show user-friendly message
4. User can try again later

## Configuration

### Adjusting Retry Settings

**AI Service** (backend/app/services/ai.py):
```python
max_retries = 3  # Number of retry attempts
retry_delays = [2, 5, 10]  # Delays in seconds
```

**RAG Service** (backend/app/services/rag.py):
```python
max_retries = 3  # Number of retry attempts
retry_delays = [1, 3, 5]  # Delays in seconds
```

### Recommended Settings

**Low Traffic**:
- Retries: 2
- Delays: [1, 3]

**Medium Traffic** (Current):
- Retries: 3
- Delays: [2, 5, 10] (AI) / [1, 3, 5] (Embeddings)

**High Traffic**:
- Retries: 4
- Delays: [2, 5, 10, 20]

## Monitoring

### Log Messages

**Successful Retry**:
```
⏳ Rate limit hit (429), retrying in 2s (attempt 1/3)...
✅ Generated response: 1234 chars
```

**Failed After Retries**:
```
⏳ Rate limit hit (429), retrying in 2s (attempt 1/3)...
⏳ Rate limit hit (429), retrying in 5s (attempt 2/3)...
⏳ Rate limit hit (429), retrying in 10s (attempt 3/3)...
❌ Rate limit exceeded after 3 attempts
```

**Embedding Fallback**:
```
⏳ Embedding rate limit (429), retrying in 1s (attempt 1/3)...
⏳ Embedding rate limit (429), retrying in 3s (attempt 2/3)...
⏳ Embedding rate limit (429), retrying in 5s (attempt 3/3)...
❌ Embedding rate limit exceeded after 3 attempts, using fallback
✅ Using hash-based embedding
```

## Best Practices

### For Users
1. **Be patient** - First retry happens automatically
2. **Don't spam** - Multiple rapid requests increase rate limits
3. **Try again** - If all retries fail, wait a minute and retry

### For Developers
1. **Monitor logs** - Watch for frequent rate limits
2. **Adjust delays** - Increase if rate limits persist
3. **Consider caching** - Cache embeddings to reduce API calls
4. **Upgrade plan** - Consider Mistral paid tier for higher limits

## Future Enhancements

Potential improvements:
- [ ] Adaptive backoff based on rate limit headers
- [ ] Request queuing system
- [ ] Embedding cache to reduce API calls
- [ ] Multiple API key rotation
- [ ] Circuit breaker pattern
- [ ] Rate limit prediction
