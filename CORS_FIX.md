# CORS Error Fix - ServiceContainer Initialization

## Problem

After the decoupling implementation, the API was returning 500 Internal Server Error which triggered CORS errors in the browser:

```
Access to fetch at 'https://15-237-208-231.sslip.io/api/v1/ai/chat/stream' 
from origin 'https://benchside.vercel.app' has been blocked by CORS policy
```

## Root Cause

The ServiceContainer was being initialized on **every API request** instead of once at application startup. This caused:

1. **Multiple initialization attempts** - Each endpoint dependency injection was calling `container.initialize(db)`
2. **Service instantiation conflicts** - Services were being created multiple times with different database connections
3. **500 errors** - The conflicts caused runtime errors
4. **CORS errors** - The 500 errors happened before CORS middleware could add headers

## Solution

### 1. Initialize Container at App Startup (`main.py`)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup code ...
    
    # Initialize ServiceContainer with database ONCE
    from app.core.container import container
    from app.core.database import db as db_manager
    container.initialize(db_manager.get_client())
    print("✅ ServiceContainer initialized with all services")
    
    # ... rest of startup code ...
```

### 2. Update Services to Not Initialize Container

**Before (WRONG):**
```python
@property
def container(self):
    if self._container is None:
        self._container = container.initialize(self._db) if self._db else container
    return self._container
```

**After (CORRECT):**
```python
@property
def def container(self):
    """Get container - should be initialized at app startup"""
    if self._container is None:
        # Don't try to initialize - should already be initialized
        self._container = container
    return self._container
```

### 3. Update API Endpoints with Fallback Check

```python
def get_ai_service(db: Client = Depends(get_db)) -> AIService:
    """Get AI service from container"""
    # Container should be initialized at app startup
    # Fallback check for safety
    if not service_container.is_initialized():
        service_container.initialize(db)
    return service_container.get('ai_service')
```

## Files Modified

1. **`main.py`** - Added container initialization in `lifespan()`
2. **`app/services/ai.py`** - Removed `container.initialize()` call
3. **`app/services/chat_orchestrator.py`** - Removed `container.initialize()` call
4. **`app/services/research_tasks.py`** - Removed `container.initialize()` call
5. **`app/api/v1/endpoints/ai.py`** - Added `is_initialized()` check
6. **`app/api/v1/endpoints/health.py`** - Added `is_initialized()` check

## Verification

```bash
cd backend
.venv/bin/python -c "
from app.core.container import container
from app.core.database import db

# Simulate app startup
container.initialize(db.get_client())
print('✅ Container initialized')

# Try to initialize again - should be skipped
container.initialize(db.get_client())
print('✅ Second initialize() safely skipped')

# Get services
ai = container.get('ai_service')
print('✅ Got ai_service')

chat = container.get('chat_service')
print('✅ Got chat_service')
"
```

## Expected Behavior After Fix

1. **App Startup**: Container initializes once with all 24 services
2. **API Requests**: Services retrieved from already-initialized container
3. **No 500 Errors**: Services properly instantiated
4. **CORS Headers**: Added correctly by middleware
5. **Frontend Works**: No CORS errors in browser

## Deployment

After deploying these changes:

1. **Restart the PM2 service** on VPS:
   ```bash
   ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 restart benchside-api"
   ```

2. **Verify logs**:
   ```bash
   ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 logs benchside-api --lines 50 --nostream"
   ```

3. **Look for**:
   ```
   ✅ Database initialized
   ✅ ServiceContainer initialized with all services
   ```

4. **Test frontend**: Open https://benchside.vercel.app and try a chat request

## Prevention

To prevent this issue in the future:

1. **Always initialize container at app startup** - Not in request handlers
2. **Use `is_initialized()` check** - As fallback in dependency injection
3. **Never call `container.initialize()` in services** - Services should only read from container
4. **Test after deployment** - Always verify with PM2 logs

---

*Fixed: 2026-03-06*
*Issue: CORS error after decoupling implementation*
