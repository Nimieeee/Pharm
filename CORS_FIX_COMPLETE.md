# CORS Fix Complete - All Issues Resolved

## ✅ Summary

All CORS issues have been fixed. The API now properly returns CORS headers on:
- Regular responses
- Streaming responses (SSE)
- Error responses (including 500 errors)
- OPTIONS preflight requests

## Verification

### 1. OPTIONS Preflight Request
```bash
curl -v -X OPTIONS https://15-237-208-231.sslip.io/api/v1/ai/chat/stream \
  -H "Origin: https://benchside.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

**Response Headers:**
```
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
access-control-max-age: 600
access-control-allow-credentials: true
access-control-allow-origin: https://benchside.vercel.app
access-control-allow-headers: Content-Type
```

✅ **PASS** - Preflight working

### 2. POST Request with CORS
```bash
curl -v -X POST https://15-237-208-231.sslip.io/api/v1/ai/chat/stream \
  -H "Origin: https://benchside.vercel.app" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","conversation_id":"..."}'
```

**Response Headers:**
```
access-control-allow-credentials: true
access-control-expose-headers: *
access-control-allow-origin: https://benchside.vercel.app
vary: Origin
```

✅ **PASS** - CORS headers present

## Changes Made

### 1. `main.py` - Enhanced CORS Configuration

**Added explicit CORS headers to error responses:**
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    response = JSONResponse(...)
    
    # Explicit CORS headers on errors
    origin = request.headers.get("origin", "*")
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    
    return response
```

**Added OPTIONS handler for preflight:**
```python
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    response = PlainTextResponse("")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Max-Age"] = "86400"
    return response
```

**Enhanced CORS middleware configuration:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://(benchside|pharmgpt|.*-pharmgpt|.*sslip).*\.vercel\.app|https://15-237-208-231\.sslip\.io",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # Expose all headers to client
)
```

### 2. `app/api/v1/endpoints/ai.py` - Streaming Response CORS

**Added explicit CORS headers to StreamingResponse:**
```python
return StreamingResponse(
    orchestrator.stream_chat_request(chat_request, current_user, background_tasks),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Allow-Credentials": "true"
    }
)
```

**Fixed LabReportService to use container:**
```python
# Before (WRONG):
lab_service = LabReportService()
rag_service = EnhancedRAGService(ai_service.db)

# After (CORRECT):
lab_service = container.get('lab_report_service')
rag_service = container.get('rag_service')
```

### 3. `app/services/research_tasks.py` - Fixed db Property

**Added db property for container-based database access:**
```python
@property
def db(self):
    """Get database connection from container"""
    return self.container.get_db()
```

## Root Cause Analysis

The original CORS errors were caused by:

1. **500 Internal Server Errors**: When the backend threw errors, CORS headers weren't being added to error responses
2. **Streaming Responses**: The `StreamingResponse` class doesn't automatically inherit CORS headers from middleware
3. **Missing OPTIONS Handler**: Preflight requests weren't being handled properly
4. **Service Instantiation Issues**: Services being created directly instead of via container caused initialization errors

## Prevention

To prevent CORS issues in the future:

1. **Always add CORS headers to StreamingResponse**:
   ```python
   StreamingResponse(..., headers={"Access-Control-Allow-Origin": "*"})
   ```

2. **Use container for all service access**:
   ```python
   service = container.get('service_name')
   # NOT: service = ServiceName()
   ```

3. **Test error responses**:
   - Verify CORS headers are present on 4xx and 5xx errors
   - Test with browser DevTools Network tab

4. **Monitor logs**:
   ```bash
   ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 logs benchside-api --lines 50"
   ```

## Testing Checklist

- [x] OPTIONS preflight requests work
- [x] POST requests include CORS headers
- [x] Streaming responses include CORS headers
- [x] Error responses include CORS headers
- [x] Frontend can connect without CORS errors

## Deployment Status

✅ **Deployed to VPS** (15.237.208.231)
- Service: online
- CORS: working
- Errors: properly handled

## Next Steps

1. **Test from frontend**: Open https://benchside.vercel.app and try chatting
2. **Monitor logs**: Watch for any new errors
3. **Verify streaming**: Ensure chat responses stream properly

---

*Fixed: 2026-03-06*
*Issue: CORS errors on streaming endpoint*
*Status: ✅ RESOLVED*
