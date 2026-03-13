# Implementation Plan — Post-Audit Fixes

> **Based on**: [mega_plan_full_audit.md](file:///Users/mac/.gemini/antigravity/brain/6ee91e3d-18de-414d-8d7e-743d9139ae2d/mega_plan_full_audit.md)
> **Priority**: P0 bugs first → CORS → Features → Cleanup

---

## User Review Required

> [!CAUTION]
> **405 Method Not Allowed on 3 endpoints** — All hub features (ADMET Lab, Creation Studio slides/docs) are broken in production due to double path prefixes. This is the highest priority fix.

> [!IMPORTANT]
> **BitNet decision needed** — The routing infrastructure returns `"local"` but nothing handles it. Plan proposes **Option 3 (Defer)**: add graceful fallback so `"local"` routes to Groq/Pollinations. Awaiting your confirmation.

---

## Sprint A: Fix 405 Errors (P0 — Critical)

### Root Cause

The [api.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/api.py) router adds a prefix, AND the endpoint files repeat that prefix in their route decorators:

```
api.py:  api_router.include_router(admet.router, prefix="/admet")
admet.py: @router.post("/admet/analyze")
Result:   /api/v1/admet/admet/analyze  ← WRONG (double prefix)
Frontend: /api/v1/admet/analyze        ← What the frontend calls (404/405)
```

Same pattern affects [slides.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/slides.py) and [docs.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/docs.py).

### Fix

#### [MODIFY] [admet.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/admet.py)

Strip the redundant `/admet` prefix from all route decorators:

```diff
- @router.post("/admet/analyze")
+ @router.post("/analyze")

- @router.get("/admet/svg")
+ @router.get("/svg")

- @router.get("/admet/export")
+ @router.get("/export")

- @router.get("/admet/wash")
+ @router.get("/wash")
```

#### [MODIFY] [slides.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/slides.py)

```diff
- @router.post("/slides/outline")
+ @router.post("/outline")

- @router.post("/slides/generate")
+ @router.post("/generate")

- @router.get("/slides/download/{job_id}")
+ @router.get("/download/{job_id}")
```

#### [MODIFY] [docs.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/docs.py)

```diff
- @router.post("/docs/outline")
+ @router.post("/outline")

- @router.post("/docs/generate")
+ @router.post("/generate")

- @router.get("/docs/download/{job_id}")
+ @router.get("/download/{job_id}")
```

---

## Sprint B: CORS Investigation & Hardening (P0)

### CORS Issues Found

| Issue | Where | Severity | Fix |
|:---|:---|:---|:---|
| [config.py](file:///Users/mac/Desktop/phhh/backend/app/core/config.py) line 80 default string missing Capacitor origins | [config.py](file:///Users/mac/Desktop/phhh/backend/app/core/config.py) | Medium | Add `capacitor://localhost,http://localhost` to default string |
| `androidScheme: 'https'` missing | [capacitor.config.ts](file:///Users/mac/Desktop/phhh/frontend/capacitor.config.ts) | Medium | Add `androidScheme: 'https'` |
| SSE streams may not include CORS headers | [slides.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/slides.py), [docs.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/docs.py) use `EventSourceResponse` | High | Verify `sse_starlette` passes CORS headers through middleware |
| OPTIONS preflight returns `Access-Control-Allow-Origin: *` | [main.py](file:///Users/mac/Desktop/phhh/backend/main.py) line 124 | Low | Replace `*` with actual origin from request header for credentialed requests |
| File upload (SDF) CORS | New endpoint | Medium | Ensure `multipart/form-data` Content-Type is in `allow_headers` |

### Fixes

#### [MODIFY] [config.py](file:///Users/mac/Desktop/phhh/backend/app/core/config.py)

```diff
- ALLOWED_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://localhost:5173,https://pharmgpt.netlify.app,https://pharmgpt.vercel.app,https://pharmgpt-frontend.vercel.app"
+ ALLOWED_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://localhost:5173,capacitor://localhost,http://localhost,https://pharmgpt.netlify.app,https://pharmgpt.vercel.app,https://pharmgpt-frontend.vercel.app,https://benchside.vercel.app"
```

#### [MODIFY] [capacitor.config.ts](file:///Users/mac/Desktop/phhh/frontend/capacitor.config.ts)

```diff
  server: {
    cleartext: true,
-   url: undefined
+   url: undefined,
+   androidScheme: 'https'
  }
```

#### [MODIFY] [main.py](file:///Users/mac/Desktop/phhh/backend/main.py) — OPTIONS handler

```diff
- response.headers["Access-Control-Allow-Origin"] = "*"
+ origin = request.headers.get("origin", "*")
+ response.headers["Access-Control-Allow-Origin"] = origin
```

Add [request](file:///Users/mac/Desktop/phhh/backend/tests/regression/test_router_services.py#209-212) parameter to the handler signature.

---

## Sprint C: ADMET Batch / SDF Support (P1)

### Current State
- Only accepts `{"smiles": "single_string"}` via POST
- No SDF file upload, no multi-molecule support

### Changes

#### [MODIFY] [admet.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/admet.py)

Add a new batch endpoint:

```python
@router.post("/batch")
async def analyze_batch(
    file: UploadFile = File(None),
    smiles_list: Optional[str] = Form(None), # JSON string of SMILES array
    current_user: User = Depends(get_current_user),
    admet_service = Depends(get_admet_service)
):
    """
    Batch ADMET analysis.
    Accepts: SDF file upload OR JSON array of SMILES strings.
    Returns: Array of results per molecule.
    """
```

#### [MODIFY] [admet_service.py](file:///Users/mac/Desktop/phhh/backend/app/services/admet_service.py)

- Add `extract_smiles_from_sdf(content: bytes) -> List[str]`
  - Use `rdkit.Chem.SDMolSupplier` to iterate through molecules
  - Convert each to SMILES using `Chem.MolToSmiles`
- Add `analyze_batch(smiles_list: List[str]) -> List[Dict[str, Any]]`
  - Limit batch size (e.g., max 20 molecules per request)
  - Execute [predict_admet](file:///Users/mac/Desktop/phhh/backend/app/services/admet_service.py#118-149) in sequence with small delay (rate limiting)
  - Aggregate reports and structured data

#### [MODIFY] [LabDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/LabDashboard.tsx)

- **UI State**: Add `batchResults: ADMETResult[]` and `isBatchMode`.
- **Upload**: Integrate [UploadZone](file:///Users/mac/Desktop/phhh/frontend/src/components/genetics/UploadZone.tsx#14-139) pattern for [.sdf](file:///Users/mac/Desktop/phhh/top_20_mmgbsa.sdf) files.
- **Display**: If multiple results exist, show a "Molecule List" sidebar or tabs to switch between analyzed molecules.
- **Export**: Add "Export All (ZIP/Combined CSV)" functionality.

---

## Sprint D: Theme Toggle + Back Button (P1)

### Current State
- [HubLayout.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/HubLayout.tsx) already has a back button (line 47-53: `→ /chat`)
- [ThemeToggle.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/ui/ThemeToggle.tsx) exists and is used elsewhere
- Hub pages do NOT use theme toggle or respect light/dark mode

### Changes

#### [MODIFY] [HubLayout.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/HubLayout.tsx)

- Import and add [ThemeToggle](file:///Users/mac/Desktop/phhh/frontend/src/components/ui/ThemeToggle.tsx#10-110) component to the header area (next to title)
- Update back button text from "Back to Research Chat" to "← Home" and add a secondary "← Chat" option
- Make the hub background responsive to theme (currently hardcoded `bg-[#0a0a0b]`)

```diff
+ import { ThemeToggle } from '@/components/ui/ThemeToggle';
+ import { useTheme } from '@/lib/theme-context';

  // In the header, add ThemeToggle:
  <div className="flex items-center justify-between mb-8">
    <Link href="/chat">...</Link>
+   <ThemeToggle />
  </div>

  // Update background to be theme-aware:
- <div className="min-h-screen bg-[#0a0a0b] text-slate-200">
+ <div className={`min-h-screen ${theme === 'dark' ? 'bg-[#0a0a0b] text-slate-200' : 'bg-white text-slate-800'}`}>
```

---

## Sprint E: BitNet Dead Code (P2 — Deferred)

### Proposed Approach: **Option 3 — Graceful Fallback**

#### [MODIFY] [router_service.py](file:///Users/mac/Desktop/phhh/backend/app/services/router_service.py)

Add fallback logic so `"local"` never reaches the caller without a handler:

```diff
  def route(self, prompt, token_count, mode):
      ...
-     return self._route_fast(complexity, queue_busy)
+     result = self._route_fast(complexity, queue_busy)
+     # Fallback: if local isn't available, route to groq
+     if result == "local" and not self._is_local_available():
+         return "groq"
+     return result
```

Add helper:
```python
def _is_local_available(self) -> bool:
    """Check if local BitNet server is reachable"""
    # For now, local is not deployed
    return False
```

---

## Sprint F: Fix 26 Backend Regression Tests (P1)

Already planned in [implementation_plan_sprint3.md](file:///Users/mac/.gemini/antigravity/brain/6ee91e3d-18de-414d-8d7e-743d9139ae2d/implementation_plan_sprint3.md). Key items:
- Update [test_service_integration.py](file:///Users/mac/Desktop/phhh/backend/tests/regression/test_service_integration.py) expected services list (already done)
- Fix [MermaidProcessor](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/mermaid_processor.py#22-421) label quoting edge cases
- Fix [PromptProcessor](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/prompt_processor.py#16-153) HLA detection case sensitivity
- Adjust performance test thresholds for VPS

---

## Verification Plan

### Automated Tests

```bash
# 1. Backend regression suite on VPS (target: 0 failures)
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 \
  "cd /var/www/benchside-backend/backend && export PYTHONPATH=. && \
   source .venv/bin/activate && pytest tests/regression/ -v"

# 2. Frontend build (catches TypeScript errors)
cd /Users/mac/Desktop/phhh/frontend && npm run build

# 3. CORS preflight verification
curl -v -H "Origin: capacitor://localhost" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS \
  https://15-237-208-231.sslip.io/api/v1/admet/analyze

# 4. ADMET endpoint test (should return 200, not 405)
curl -X POST https://15-237-208-231.sslip.io/api/v1/admet/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"smiles": "CC(=O)Oc1ccccc1C(=O)O"}'

# 5. Slides endpoint test
curl -X POST https://15-237-208-231.sslip.io/api/v1/slides/outline \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"topic": "test"}'
```

### Manual Verification
1. Open `https://benchside.vercel.app/lab` → Enter Aspirin SMILES → Verify analysis completes (no 405)
2. Open `https://benchside.vercel.app/studio` → Select Slides → Enter topic → Verify outline generates (no 405)
3. Verify theme toggle appears on all hub pages and switches correctly
4. Test SDF file upload in ADMET Lab with a multi-molecule [.sdf](file:///Users/mac/Desktop/phhh/top_20_mmgbsa.sdf) file
5. Verify back button navigates to `/chat` from all hub pages
