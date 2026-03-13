# Fix Plan: Console Error Investigation (2026-03-13)

## Executive Summary

Based on systematic investigation of browser console errors, three critical issues have been identified:

1. **DeepLinkHandler URL Constructor Error** - Crashes when `data.url` is null/undefined
2. **Multiple 401 Unauthorized Errors** - Missing authentication headers on protected endpoints
3. **ADMET SVG 400 Error** - Potential SMILES encoding issues

**Status**: Investigation Complete | **Estimated Fix Time**: 2-3 hours | **Regression Risk**: Low

---

## Issue 1: DeepLinkHandler URL Constructor Error

### Problem Statement
**Error**: `TypeError: Failed to construct 'URL': Invalid URL`
**Location**: `frontend/src/components/DeepLinkHandler.tsx:15, 27`
**Impact**: High - Causes unhandled promise rejection

### Root Cause Analysis
The component attempts to construct a URL from `data.url` without validating:
- Whether `data.url` exists
- Whether `data.url` is a valid string
- Whether `data.url` is a valid URL format

When Capacitor's `App.addListener` fires with an invalid or null URL, the `new URL()` constructor throws.

### Current Code
```typescript
// Line 15
const url = new URL(data.url);  // Throws if data.url is null/undefined

// Line 27  
const url = new URL(launchUrl.url);  // Throws if launchUrl.url is null/undefined
```

### Proposed Fix
```typescript
// Line 12-21: Wrap in try-catch with validation
App.addListener('appUrlOpen', (data: any) => {
  try {
    if (!data?.url || typeof data.url !== 'string') {
      console.warn('Invalid deep link data received:', data);
      return;
    }
    const url = new URL(data.url);
    const path = url.pathname;
    const search = url.search;
    router.push(`${path}${search}`);
  } catch (e) {
    console.error('Failed to process deep link:', e);
  }
});

// Line 24-32: Similar fix for initial URL
checkInitialUrl: async () => {
  try {
    const launchUrl = await App.getLaunchUrl();
    if (!launchUrl?.url || typeof launchUrl.url !== 'string') {
      return;  // No initial URL to process
    }
    const url = new URL(launchUrl.url);
    router.push(`${url.pathname}${url.search}`);
  } catch (e) {
    console.error('Failed to process initial URL:', e);
  }
}
```

### Testing Steps
1. Load app normally - should not see URL constructor error
2. Test with invalid deep link - should log warning, not crash
3. Test with valid deep link - should navigate correctly

---

## Issue 2: Multiple 401 Unauthorized Errors

### Problem Statement
**Errors**:
- `POST /api/v1/admet/analyze` - 401 Unauthorized
- `GET /api/v1/chat/gwas/lookup/{rsid}` - 401 Unauthorized
- `POST /api/v1/slides/outline` - 401 Unauthorized

**Impact**: High - Core features non-functional

### Root Cause Analysis
These endpoints require authentication via `get_current_user` dependency:

```python
# backend/app/api/v1/endpoints/admet.py:70-75
@router.post("/analyze")
async def analyze_molecule(
    request: ADMETAnalysisRequest,
    current_user: User = Depends(get_current_user),  # Requires auth!
    admet_service = Depends(get_admet_service)
):

# backend/app/api/v1/endpoints/chat.py:822-826
@router.get("/gwas/lookup/{rsid}")
async def gwas_lookup(
    rsid: str,
    current_user: User = Depends(get_current_user)  # Requires auth!
):
```

However, frontend components don't include the `Authorization` header:

```typescript
// GeneticsDashboard.tsx:70 - NO AUTH HEADER
const response = await fetch(`${API_BASE_URL}/api/v1/chat/gwas/lookup/${rsid.trim()}`);

// LabDashboard.tsx:107 - NO AUTH HEADER
const response = await fetch(`${API_BASE_URL}/api/v1/admet/analyze`, { ... });
```

### Proposed Fix

Add authentication headers following existing pattern in `GeneticsDashboard.tsx:69-72`:

```typescript
// Pattern to apply to all protected endpoints
const token = typeof window !== 'undefined' ? localStorage.getItem('sb-access-token') : null;
const headers: HeadersInit = {
  'Content-Type': 'application/json',
  ...(token ? { 'Authorization': `Bearer ${token}` } : {})
};

const response = await fetch(`${API_BASE_URL}/endpoint`, {
  method: 'POST',
  headers,
  body: JSON.stringify(data)
});
```

### Files to Modify

1. **frontend/src/components/lab/LabDashboard.tsx**
   - Line 107: ADMET analyze call
   - Line 138: ADMET export call
   - Add auth headers to both fetch calls

2. **frontend/src/components/genetics/GeneticsDashboard.tsx**
   - Line 70: GWAS lookup call
   - **Note**: Already has auth pattern on line 69-72, verify working

3. **frontend/src/components/studio/CreationStudio.tsx**
   - Lines 58, 92, 112, 144: Slides endpoints
   - Add auth headers to all slide-related fetch calls

### Testing Steps
1. Login to application
2. Navigate to Lab Dashboard → ADMET Analysis
3. Submit SMILES string → should return 200 with report
4. Navigate to Genetics Dashboard → GWAS Lookup
5. Enter rsID (e.g., "rs7903146") → should return 200 with variant data
6. Navigate to Creation Studio → Slides
7. Create outline → should work without 401

---

## Issue 3: ADMET SVG 400 Error

### Problem Statement
**Error**: `Failed to load resource: the server responded with a status of 400 (Bad Request)`
**Location**: `frontend/src/components/lab/MoleculePreview.tsx:24`
**Endpoint**: `/api/v1/admet/svg?smiles=...`

### Root Cause Analysis
The endpoint at `backend/app/api/v1/endpoints/admet.py:100-125` does NOT require authentication (no `get_current_user` dependency), so 401 is not the issue.

The 400 error suggests SMILES string validation failure. Possible causes:
1. Double URL encoding of SMILES parameter
2. Invalid SMILES characters not properly escaped
3. Missing SMILES parameter

### Current Code
```typescript
// MoleculePreview.tsx:24
const response = await fetch(`${API_BASE_URL}/api/v1/admet/svg?smiles=${encodeURIComponent(smiles)}`);
```

### Proposed Fix
Add validation before fetch and better error handling:

```typescript
const fetchSvg = async () => {
  if (!smiles || typeof smiles !== 'string') {
    setError('No SMILES string provided');
    return;
  }
  
  setIsLoading(true);
  setError(null);
  
  try {
    // Ensure SMILES is properly encoded
    const encodedSmiles = encodeURIComponent(smiles.trim());
    const response = await fetch(`${API_BASE_URL}/api/v1/admet/svg?smiles=${encodedSmiles}`);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Failed to load molecule structure: ${response.status} - ${errorText}`);
    }
    
    const data = await response.text();
    setSvg(data);
  } catch (err: any) {
    setError(err.message);
    console.error('Molecule preview error:', err);
  } finally {
    setIsLoading(false);
  }
};
```

### Backend Validation (Optional)
If issue persists, add logging to `backend/app/api/v1/endpoints/admet.py:100-125`:

```python
@router.get("/svg")
async def get_molecule_svg(
    smiles: str = Query(..., description="SMILES string"),
    admet_service = Depends(get_admet_service)
):
    logger.info(f"SVG request received for SMILES: {smiles}")
    # ... rest of function
```

### Testing Steps
1. Navigate to Lab Dashboard
2. Enter valid SMILES: "CCO" (ethanol)
3. Should display molecule structure SVG
4. Test with invalid SMILES → should show clear error message

---

## Implementation Checklist

### Phase 1: DeepLinkHandler Fix
- [ ] Modify `frontend/src/components/DeepLinkHandler.tsx`
- [ ] Add null/undefined checks for `data.url` and `launchUrl.url`
- [ ] Add try-catch blocks around URL constructor
- [ ] Test locally with browser console open

### Phase 2: Authentication Header Fixes
- [ ] Modify `frontend/src/components/lab/LabDashboard.tsx`
  - [ ] Add auth header to ADMET analyze (line 107)
  - [ ] Add auth header to ADMET export (line 138)
- [ ] Verify `frontend/src/components/genetics/GeneticsDashboard.tsx` auth
- [ ] Modify `frontend/src/components/studio/CreationStudio.tsx`
  - [ ] Add auth headers to all fetch calls

### Phase 3: SMILES Encoding Fix
- [ ] Modify `frontend/src/components/lab/MoleculePreview.tsx`
- [ ] Add SMILES validation before fetch
- [ ] Improve error handling with status codes
- [ ] Test with various SMILES strings

### Phase 4: Verification
- [ ] Run regression tests: `./run_regression.sh`
- [ ] Build frontend: `cd frontend && npm run build`
- [ ] Manual browser testing of all three features
- [ ] Check console for no new errors

---

## Failure Mode Analysis (FMA)

| Fix | Potential Failure Modes | Mitigation |
|-----|------------------------|------------|
| **DeepLinkHandler validation** | May hide legitimate Capacitor errors | Log warnings to console for debugging |
| **Auth header addition** | Token may be expired | Ensure app handles 401 with redirect to login |
| **SMILES encoding** | May double-encode already encoded strings | Only encode once, use `.trim()` first |
| **Protected endpoints** | Breaks if user not logged in | Ensure graceful handling of auth state |

---

## Regression Prevention

Per CLAUDE.md guidelines:

1. **Test-Driven**: Each fix should be testable manually
2. **Scope Discipline**: Only touch the identified files
3. **Documentation**: This plan serves as implementation guide
4. **Verification**: Run regression tests before deployment

### Pre-Deployment Checklist
- [ ] Run: `./run_regression.sh` (must pass, <10s)
- [ ] Build: `cd frontend && npm run build` (must succeed)
- [ ] Manual test all three fixed features
- [ ] Check browser console for new errors

---

## References

- CLAUDE.md Section: "Implementation Error Prevention Rules"
- Pattern: ServiceContainer for backend dependencies
- Pattern: Frontend auth header implementation

---

**Plan Created**: 2026-03-13  
**Author**: Claude (via Systematic Debugging)  
**Status**: Ready for Implementation
