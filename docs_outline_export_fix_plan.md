# Fix Plan: Document & Export Endpoints 500/404 Errors

## Investigation Summary

### Issue 1: `/api/v1/docs/outline` → 500 Internal Server Error

**Root Cause:** In `backend/app/api/v1/endpoints/docs.py` line 39, `get_doc_service()` is called without any arguments:
```python
doc_service = get_doc_service()
```

But `get_doc_service()` in `backend/app/services/doc_service.py` expects a `multi_provider` parameter:
```python
def get_doc_service(multi_provider: MultiProviderService = None) -> DocService:
```

When called without arguments, `multi_provider` is `None`, and the DocService constructor tries to use it, causing an AttributeError or similar failure.

### Issue 2: `/api/v1/ai/conversations/{id}/export/manuscript` → 404 Not Found

**Root Cause:** Route path structure conflict. The export router is mounted at `/ai` prefix:
```python
# api.py line 16
api_router.include_router(export.router, prefix="/ai", tags=["export"])
```

But the route in export.py is:
```python
@router.get("/conversations/{conversation_id}/export/manuscript")
```

This creates the path `/api/v1/ai/conversations/{conversation_id}/export/manuscript`.

However, the `ai.router` is ALSO mounted at `/ai`:
```python
# api.py line 15
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
```

FastAPI routes are matched in order of registration. Since `ai.router` is registered BEFORE `export.router`, routes from `ai.router` take precedence. If `ai.router` has any catch-all or early-matching routes, requests may not reach the export routes.

Additionally, the path structure `/conversations/{conversation_id}/export/manuscript` under `/ai` prefix is unconventional and may conflict with other conversation-related routes.

---

## Implementation Plan

### Fix 1: Document Outline Endpoint

**File:** `backend/app/api/v1/endpoints/docs.py`

**Problem:** Direct function call without dependency injection.

**Solution:** Use FastAPI Depends() pattern for proper DI.

```python
# BEFORE (line 37-39):
async def generate_doc_outline(
    request: DocOutlineRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        from app.services.doc_service import get_doc_service
        
        doc_service = get_doc_service()  # Called without arguments

# AFTER:
from app.core.container import get_container
from app.core.database import get_db
from supabase import Client

def get_doc_service_dep(db: Client = Depends(get_db)):
    """Dependency to get DocService from container"""
    container = get_container(db)
    return container.get('ai_service').multi_provider  # Get multi_provider from AI service

@router.post("/outline")
async def generate_doc_outline(
    request: DocOutlineRequest,
    current_user: User = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """Step 1: Generate editable document outline"""
    try:
        from app.services.doc_service import get_doc_service
        from app.core.container import get_container
        
        container = get_container(db)
        ai_service = container.get('ai_service')
        doc_service = get_doc_service(ai_service.multi_provider)
        
        # ... rest of function
```

### Fix 2: Export Endpoint Path Structure

**File:** `backend/app/api/v1/api.py`

**Problem:** Export router mounted at `/ai` prefix creates unconventional path and potential conflicts.

**Solution:** Move export router to its own `/export` prefix.

```python
# BEFORE (lines 15-16):
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(export.router, prefix="/ai", tags=["export"])

# AFTER:
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
```

**File:** `backend/app/api/v1/endpoints/export.py`

**Update route paths to be cleaner:**

```python
# BEFORE (line 307):
@router.get("/conversations/{conversation_id}/export/manuscript")

# AFTER (simpler path, router mounted at /export):
@router.get("/{conversation_id}/manuscript")
```

Similarly update other export routes:
```python
# BEFORE line 167:
@router.get("/conversations/{conversation_id}/export/docx")
# AFTER:
@router.get("/{conversation_id}/docx")

# BEFORE line 226:
@router.get("/conversations/{conversation_id}/export/pdf")
# AFTER:
@router.get("/{conversation_id}/pdf")
```

### Fix 3: Frontend API URL Update

**Files to check:** Frontend export-related components/hooks

Search for:
```bash
grep -rn "export/manuscript" frontend/src/
grep -rn "export/docx" frontend/src/
grep -rn "export/pdf" frontend/src/
```

Update URLs from:
- `/api/v1/ai/conversations/{id}/export/manuscript`
- `/api/v1/ai/conversations/{id}/export/docx`
- `/api/v1/ai/conversations/{id}/export/pdf`

To:
- `/api/v1/export/{id}/manuscript`
- `/api/v1/export/{id}/docx`
- `/api/v1/export/{id}/pdf`

---

## Todo Checklist

- [ ] Fix docs.py: Add proper DI for DocService
- [ ] Fix api.py: Change export router prefix from `/ai` to `/export`
- [ ] Fix export.py: Simplify route paths (remove `/conversations/{id}/export/` prefix)
- [ ] Update frontend API URLs for export endpoints
- [ ] Test docs outline endpoint
- [ ] Test export manuscript endpoint
- [ ] Run regression tests

---

## Testing Commands

```bash
# Test docs outline
curl -X POST "http://localhost:7860/api/v1/docs/outline" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"topic": "ADMET Analysis", "doc_type": "report"}'

# Test export manuscript
curl -X GET "http://localhost:7860/api/v1/export/{conversation_id}/manuscript?style=report" \
  -H "Authorization: Bearer <token>"
```

---

## Risk Assessment

**Low Risk Changes:**
- Changing export router prefix is a straightforward path change
- Frontend URL updates are simple string replacements

**Medium Risk:**
- DocService DI setup - need to ensure container is initialized correctly
- May need to verify DocService doesn't have other dependencies requiring the container

**No Breaking Changes:**
- Export endpoints are currently broken (404), so fixing them has no regression risk
- Docs outline endpoint returns 500, fixing it restores functionality