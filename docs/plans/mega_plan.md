# Mega Plan v2: Benchside Scientific Platform

> **Updated**: 2026-03-12 | **CLAUDE.md Compliance**: Full
> **Priority**: UI Polish → CORS Hardening → Export Processor → Local Inference → Capacitor Mobile

---

## Context

This plan consolidates and updates the original mega_plan based on a thorough codebase audit.
Many items previously marked as [NEW] are now implemented. This revision reflects accurate status,
adds premium UI redesign specifications, CORS hardening for Capacitor/mobile, and follows
CLAUDE.md patterns (ServiceContainer, Postprocessing, TDD, FMA) religiously.

### CoT Retrieval Evidence
```
python3 /Users/mac/Desktop/phhh/scripts/cot_retriever.py "Hub-and-spoke frontend architecture..."
# Retrieved patterns on component-based architecture, CORS middleware layering,
# and capability-based routing. Applied: layered CORS strategy, hub isolation pattern.
```

---

## Implementation Status Audit

### ✅ DONE — Backend Services
| File | Lines | Status |
|:---|:---|:---|
| `backend/app/services/admet_service.py` | 236 | ✅ Registered in container |
| `backend/app/services/router_service.py` | 129 | ✅ Registered in container |
| `backend/app/services/local_queue.py` | 93 | ✅ Registered in container |
| `backend/app/services/postprocessing/admet_processor.py` | 240 | ✅ Registered in container |
| `backend/app/services/postprocessing/prompt_processor.py` | 156 | ✅ Registered in container |
| `backend/app/services/postprocessing/mermaid_processor.py` | — | ✅ Existing |
| `backend/app/api/v1/endpoints/admet.py` | — | ✅ Existing |
| `backend/app/core/container.py` | 274 | ✅ All 5 new services registered |

### ✅ DONE — Frontend Routes & Components
| File | Lines | Status |
|:---|:---|:---|
| `frontend/src/app/lab/page.tsx` | 13 | ✅ Imports LabDashboard |
| `frontend/src/app/genetics/page.tsx` | 13 | ✅ Imports GeneticsDashboard |
| `frontend/src/app/studio/page.tsx` | 13 | ✅ Imports CreationStudio |
| `frontend/src/components/lab/LabDashboard.tsx` | 267 | ✅ Functional (ADMET input + results + CSV) |
| `frontend/src/components/genetics/GeneticsDashboard.tsx` | 298 | ✅ Functional (PharmGx + GWAS tabs) |
| `frontend/src/components/studio/CreationStudio.tsx` | 289 | ✅ Functional (Slides + Docs + SSE) |
| `frontend/src/components/chat/HandoffButton.tsx` | 62 | ✅ Functional (lab/genetics/studio) |

### ✅ DONE — Regression Tests
| File | Status |
|:---|:---|
| `backend/tests/regression/test_admet_service.py` | ✅ Exists |
| `backend/tests/regression/test_router_services.py` | ✅ Exists |
| `backend/tests/regression/test_mermaid.py` | ✅ 26 tests |
| `backend/tests/regression/test_all_services.py` | ✅ Exists |

### ❌ REMAINING — What This Plan Covers
| Item | Priority | Sprint |
|:---|:---|:---|
| UI polish for all 3 hubs (premium design) | P0 | Sprint 1 |
| CORS hardening for Capacitor/mobile | P0 | Sprint 1 |
| `export_processor.py` (missing postprocessor) | P1 | Sprint 1 |
| `multi_provider.py` model update (`claude-airforce`) | P1 | Sprint 1 |
| Frontend tests for hub components | P2 | Sprint 2 |
| `deploy_bitnet.sh` VPS script | P3 | Sprint 3 |
| Capacitor config + native plugins | P3 | Sprint 3 |

---

## Phase 1: CORS Hardening (P0)

### 1.1 Problem

Current CORS config in `main.py` covers Vercel and localhost:3000, but **missing**:
- `capacitor://localhost` (iOS WebView)
- `http://localhost` (Android WebView, no port)
- `ionic://localhost` (Ionic fallback)

The Capacitor app (`capacitor.config.ts`) is configured with `appId: 'com.benchside.app'` and `webDir: 'out'`. Without these origins, all API calls from the native app will fail with CORS errors.

### 1.2 Changes

#### [MODIFY] [main.py](file:///Users/mac/Desktop/phhh/backend/main.py)

Add Capacitor-safe origins to the explicit allowed list:

```python
# Lines 91-99: Add mobile WebView origins
allowed_origins.extend([
    "https://benchside.vercel.app",
    "https://www.benchside.vercel.app",
    "https://pharmgpt.vercel.app",
    "https://pharmgpt-frontend.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://15-237-208-231.sslip.io",
    # Capacitor/Mobile WebView origins
    "capacitor://localhost",      # iOS Capacitor
    "http://localhost",           # Android Capacitor (no port)
    "ionic://localhost",          # Ionic fallback
])
```

Update the `allow_origin_regex` to also cover Capacitor:
```python
allow_origin_regex=r"https://(benchside|pharmgpt|.*-pharmgpt|.*sslip).*\.vercel\.app|https://15-237-208-231\.sslip\.io|capacitor://localhost|ionic://localhost",
```

#### [MODIFY] [config.py](file:///Users/mac/Desktop/phhh/backend/app/core/config.py)

Add Capacitor origins to the default ALLOWED_ORIGINS fallback:
```python
# Line 80
ALLOWED_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://localhost:5173,capacitor://localhost,http://localhost,https://benchside.vercel.app"
```

And in the fallback list (lines 99-106 and 112-118):
```python
"capacitor://localhost",
"http://localhost",
```

#### [MODIFY] [capacitor.config.ts](file:///Users/mac/Desktop/phhh/frontend/capacitor.config.ts)

Add server config for API proxying:
```typescript
const config: CapacitorConfig = {
  appId: 'com.benchside.app',
  appName: 'Benchside',
  webDir: 'out',
  server: {
    // Allow mixed content for local dev
    cleartext: true,
    // Use the production API URL
    url: undefined, // Uses webDir by default; set for live reload
  },
};
```

---

## Phase 2: UI Polish — Premium Hub Redesign (P0)

### 2.1 Design Principles

All three hubs currently work but look basic — plain card layouts with minimal visual hierarchy.
The redesign targets a **premium, dark-mode-first aesthetic** with:

- **Glassmorphism** cards with `backdrop-blur` and subtle borders
- **Color-coded hub identities**: Lab = Amber, Genetics = Purple, Studio = Teal
- **Micro-animations** on every interaction (hover lift, focus glow, result slide-in)
- **Responsive grid layouts** that collapse gracefully on mobile (375px target)
- **Empty states** with illustrated placeholders instead of blank space
- **Skeleton loaders** instead of spinner-only loading states

### 2.2 Lab Dashboard Redesign

#### [MODIFY] [LabDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/LabDashboard.tsx)

**Current**: Single-column layout, basic input → raw markdown dump.

**Redesigned Structure**:
```
┌─────────────────────────────────────────────────────────┐
│  🧪 ADMET Lab                                    [?]   │
│  Predict drug properties from molecular structure       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─ Molecule Input ──────────────────────────────────┐  │
│  │  [SMILES input ___________________________] [▶]   │  │
│  │  Try: [Aspirin] [Caffeine] [Penicillin] [Diazepam]│  │
│  │  ── or ──                                         │  │
│  │  [📋 Paste from clipboard] [📁 Upload .sdf/.mol]  │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─ Molecule Preview ─────┐  ┌─ Quick Summary ───────┐ │
│  │                        │  │ Lipinski: ✅ Pass      │ │
│  │   [SVG Structure]      │  │ PAINS: ✅ Clean       │ │
│  │                        │  │ Bioavail: 0.85        │ │
│  │   MW: 180.16 g/mol     │  │ LogP: 1.2            │ │
│  │   Formula: C₉H₈O₄     │  │ Solubility: High     │ │
│  └────────────────────────┘  └───────────────────────┘ │
│                                                         │
│  ┌─ ADMET Properties (Grid) ────────────────────────┐  │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐          │  │
│  │ │Absorption│ │Distribut.│ │Metabolism│          │  │
│  │ │ Caco-2 ✅│ │ BBB: ❌  │ │ CYP3A4 ⚠│          │  │
│  │ │ HIA: 95% │ │ PPB: 80% │ │ CYP2D6 ✅│          │  │
│  │ └──────────┘ └──────────┘ └──────────┘          │  │
│  │ ┌──────────┐ ┌──────────┐                        │  │
│  │ │Excretion │ │Toxicity  │  [Export CSV] [Share]  │  │
│  │ │ T½: 4.5h │ │ hERG: ✅ │                        │  │
│  │ │ CL: Med  │ │ AMES: ✅ │                        │  │
│  │ └──────────┘ └──────────┘                        │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Key changes**:
1. **Add molecule SVG preview** — render the SVG from `/api/v1/admet/svg` in a side panel
2. **ADMET property grid** — parse the markdown report into structured cards with color-coded badges (✅ green, ⚠ amber, ❌ red)
3. **Quick summary sidebar** — extract Lipinski, PAINS, key metrics
4. **Skeleton loader** — show animated placeholder cards during analysis
5. **Clipboard paste + .sdf upload** — add alternative input methods
6. **Responsive** — stack preview/summary vertically on mobile

#### [NEW] [ADMETPropertyCard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/ADMETPropertyCard.tsx)

Reusable card for individual ADMET categories (Absorption, Distribution, etc.) with:
- Header with icon and category name
- List of properties with status badges
- Hover tooltip with detailed explanation
- Glassmorphism styling

#### [NEW] [MoleculePreview.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/MoleculePreview.tsx)

SVG molecule renderer component:
- Fetches SVG from backend `/api/v1/admet/svg`
- Dark mode inversion filter
- Zoom on hover
- Download SVG button

### 2.3 Genetics Dashboard Redesign

#### [MODIFY] [GeneticsDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/genetics/GeneticsDashboard.tsx)

**Current**: Tab selector + basic input → component render.

**Redesigned Structure**:
```
┌─────────────────────────────────────────────────────────┐
│  🧬 Genetics Hub                                       │
│  Pharmacogenomics and variant analysis                  │
├─────────────────────────────────────────────────────────┤
│  [◉ PharmGx Report]  [○ GWAS Lookup]                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─ Upload Zone ─────────────────────────────────────┐  │
│  │          ┌────────────────────────┐                │  │
│  │          │  📂 Drop your 23andMe  │                │  │
│  │          │  or AncestryDNA file   │                │  │
│  │          │  here, or click to     │                │  │
│  │          │  browse                │                │  │
│  │          └────────────────────────┘                │  │
│  │  Supported: 23andMe (.txt), AncestryDNA (.txt)    │  │
│  │  🔒 Your data never leaves this session           │  │
│  └───────────────────────────────────────────────────┘  │
│                                                         │
│  ┌─ Results ─────────────────────────────────────────┐  │
│  │  ┌─ Drug Response ──┐  ┌─ Risk Variants ───────┐ │  │
│  │  │ Warfarin: ⚠ Slow │  │ CYP2C19 *4/*4        │ │  │
│  │  │ Clopidogrel: ❌  │  │ → Poor metabolizer   │ │  │
│  │  │ Simvastatin: ✅  │  │ → Avoid clopidogrel  │ │  │
│  │  └──────────────────┘  └──────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Key changes**:
1. **Drag-and-drop upload zone** with dashed border, icon, and privacy notice
2. **Structured result cards** for drug responses (instead of raw component render)
3. **Risk badges** with color coding per metabolizer status
4. **GWAS tab**: add Manhattan-plot-style result visualization with LLM-generated clinical context
5. **Example variant chips** with gene name + trait tooltip (already exists, polish styling)

#### [NEW] [UploadZone.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/genetics/UploadZone.tsx)

Reusable drag-and-drop file upload:
- Dashed border with icon
- File type validation
- Progress indicator
- Privacy badge ("🔒 Local processing only")

### 2.4 Creation Studio Redesign

#### [MODIFY] [CreationStudio.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/studio/CreationStudio.tsx)

**Current**: Type selector → topic input → outline editor → progress → download.

**Redesigned Structure**:
```
┌─────────────────────────────────────────────────────────┐
│  ✨ Creation Studio                                     │
│  AI-powered slides and documents                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────┐  ┌──────────────────────┐    │
│  │   📊 Presentation    │  │   📄 Document         │    │
│  │                      │  │                       │    │
│  │  Generate slides     │  │  Create structured    │    │
│  │  with AI images      │  │  reports & manuscripts │    │
│  │                      │  │                       │    │
│  │  [Selected ◉]        │  │  [Select ○]           │    │
│  └──────────────────────┘  └──────────────────────┘    │
│                                                         │
│  Topic: [____________________________________] [Go ▶]  │
│                                                         │
│  Recent: [Drug Resistance...] [CRISPR Review...]       │
│                                                         │
├──── Outline Editor (when generated) ────────────────────┤
│  Side-by-side: Outline tree ↔ Live preview             │
└─────────────────────────────────────────────────────────┘
```

**Key changes**:
1. **Larger type selector cards** with illustrations (already exists, polish with gradients)
2. **Recent topics** — store last 5 topics in localStorage
3. **Side-by-side preview** during outline editing
4. **Progress bar** with step labels instead of generic spinner
5. **Download options** — PPTX, PDF, DOCX format selector

### 2.5 Shared UI Components

#### [NEW] [HubLayout.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/HubLayout.tsx)

Shared layout wrapper for all hubs:
- Consistent header with hub icon, title, description
- Back-to-chat navigation link
- Responsive padding and max-width
- Glassmorphism background

#### [NEW] [SkeletonLoader.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/SkeletonLoader.tsx)

Animated skeleton placeholder for loading states:
- Card skeleton, text skeleton, grid skeleton variants
- Consistent pulse animation
- Dark mode compatible

#### [NEW] [StatusBadge.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/StatusBadge.tsx)

Color-coded status indicator:
- `success` (green), `warning` (amber), `danger` (red), `info` (blue)
- Icon + text
- Tooltip for details

---

## Phase 3: Missing Backend Components (P1)

### 3.1 Export Processor

#### [NEW] [export_processor.py](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/export_processor.py)

```python
class ExportProcessor:
    """Generic export format processing — CLAUDE.md Postprocessing Pattern."""

    def sanitize_svg(self, svg_content: str) -> str:
        """Remove potentially harmful SVG elements (script, onload, etc.)."""
        pass

    def format_csv(self, data: list, columns: list) -> str:
        """Format data as CSV with proper escaping."""
        pass

    def format_json_export(self, data: dict) -> str:
        """Pretty-print JSON for export."""
        pass

export_processor = ExportProcessor()  # Singleton
```

#### [MODIFY] [container.py](file:///Users/mac/Desktop/phhh/backend/app/core/container.py)

Register: `self._services['export_processor'] = export_processor`

#### [MODIFY] [__init__.py](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/__init__.py)

Export: `from .export_processor import ExportProcessor, export_processor`

### 3.2 Multi-Provider Model Update

#### [MODIFY] [multi_provider.py](file:///Users/mac/Desktop/phhh/backend/app/services/multi_provider.py)

Update Pollinations model from `gemini-fast` to `claude-airforce` for elite modes only:
```python
models={
    "fast": "gemini-fast",           # Keep fast for low-latency
    "detailed": "claude-airforce",   # Upgrade for reasoning
    "deep_research": "claude-airforce",
    "deep_research_elite": "claude-airforce",  # Verified 200k tokens
    "deep_research_single_pass": "gemini-fast", # Keep fast
},
```

> **Rationale**: Testing confirmed `claude-airforce` handles 200k tokens reliably and outperforms
> `gemini-fast` (which hit Vertex AI Resource Exhausted at the same load). Keep `gemini-fast`
> for fast/single-pass modes where latency matters more than reasoning depth.

---

## Phase 4: Testing Strategy (TDD Compliance)

### 4.1 New Regression Tests Required

#### [NEW] [test_export_processor.py](file:///Users/mac/Desktop/phhh/backend/tests/regression/test_export_processor.py)

```python
class TestExportProcessor:
    def test_svg_sanitization_removes_script_tags(self):
        """SVG with <script> tags must be sanitized."""
        pass

    def test_csv_format_escapes_commas(self):
        """CSV values containing commas must be quoted."""
        pass

    def test_csv_format_handles_unicode(self):
        """CSV must handle UTF-8 characters correctly."""
        pass
```

#### [NEW] [test_cors_headers.py](file:///Users/mac/Desktop/phhh/backend/tests/regression/test_cors_headers.py)

```python
class TestCORSHeaders:
    def test_capacitor_origin_allowed(self):
        """Requests from capacitor://localhost must receive CORS headers."""
        pass

    def test_vercel_origin_allowed(self):
        """Requests from benchside.vercel.app must receive CORS headers."""
        pass

    def test_unknown_origin_rejected(self):
        """Requests from unknown origins must not receive CORS headers."""
        pass

    def test_error_responses_include_cors(self):
        """Even 500 error responses must include CORS headers."""
        pass
```

### 4.2 Existing Tests to Verify

```bash
# Run existing regression suite (must pass before changes)
cd backend && source .venv/bin/activate && pytest tests/regression/ -v

# Run frontend build (catches type errors from new components)
cd frontend && npm run build
```

---

## Phase 5: Failure Mode Analysis

### 5.1 CORS Risks

| Risk | Likelihood | Impact | Mitigation |
|:---|:---|:---|:---|
| Capacitor origin blocked | High (if not fixed) | Critical | Add `capacitor://localhost` to allowed list |
| OPTIONS preflight conflict | Low | Medium | Current wildcard `*` handler covers this |
| CORS on SSE streams | Medium | High | Verify `ai.py` SSE headers include CORS |
| Mixed content on iOS | Medium | Medium | Use HTTPS API URL in production builds |

### 5.2 UI Risks

| Risk | Likelihood | Impact | Mitigation |
|:---|:---|:---|:---|
| Mobile layout breakage (≤375px) | Medium | High | Test on iPhone SE viewport, add responsive breakpoints |
| SVG rendering in dark mode | Medium | Low | Add CSS `filter: invert()` for dark mode SVGs |
| Skeleton flash on fast responses | Low | Low | Add 200ms minimum display time |
| Handoff data loss on navigation | Medium | High | Use URL params for data, not session state |

### 5.3 Model Risks

| Risk | Likelihood | Impact | Mitigation |
|:---|:---|:---|:---|
| `claude-airforce` rate limited | Medium | Medium | Fallback chain in `multi_provider.py` handles this |
| Empty response at 200k+ tokens | Known | Medium | Document as hard limit, warn users in UI |

---

## Phase 6: Verification Plan

### 6.1 Automated Tests

```bash
# 1. Run full regression suite
cd backend && source .venv/bin/activate && pytest tests/regression/ -v

# 2. Check for circular imports
cd backend && python -c "from app.services.postprocessing.export_processor import export_processor; print('OK')"

# 3. Frontend build (catches type errors)
cd frontend && npm run build

# 4. CORS test (manual curl)
curl -v -H "Origin: capacitor://localhost" \
  -H "Access-Control-Request-Method: POST" \
  -X OPTIONS \
  https://15-237-208-231.sslip.io/api/v1/admet/analyze
# Expected: Access-Control-Allow-Origin: capacitor://localhost
```

### 6.2 Manual Verification

1. **CORS**: Open Benchside in iOS simulator via Capacitor → attempt ADMET analysis → verify no CORS errors in Safari Web Inspector
2. **Lab UI**: Navigate to `/lab` → enter Aspirin SMILES → verify SVG preview renders, ADMET grid shows colored badges, CSV export downloads
3. **Genetics UI**: Navigate to `/genetics` → drag-drop a 23andMe file → verify upload zone animates, results render in structured cards
4. **Studio UI**: Navigate to `/studio` → type topic → verify outline generates, progress bar shows steps
5. **Handoff**: In `/chat`, ask "Analyze aspirin" → verify HandoffButton appears → click "Open in Lab" → verify SMILES is pre-filled
6. **Mobile**: Resize browser to 375px → verify all 3 hubs are usable without horizontal scroll

---

## Phase 7: File Changes Summary

### Backend — New Files
| File | Purpose |
|:---|:---|
| `backend/app/services/postprocessing/export_processor.py` | Generic export formatting (SVG sanitize, CSV, JSON) |
| `backend/tests/regression/test_export_processor.py` | Export processor tests |
| `backend/tests/regression/test_cors_headers.py` | CORS header verification tests |

### Backend — Modified Files
| File | Change |
|:---|:---|
| `backend/main.py` | Add Capacitor CORS origins |
| `backend/app/core/config.py` | Add Capacitor to default ALLOWED_ORIGINS |
| `backend/app/core/container.py` | Register `export_processor` |
| `backend/app/services/postprocessing/__init__.py` | Export `export_processor` |
| `backend/app/services/multi_provider.py` | Update Pollinations models (`claude-airforce` for detailed/elite) |

### Frontend — New Files
| File | Purpose |
|:---|:---|
| `frontend/src/components/lab/ADMETPropertyCard.tsx` | ADMET category card with badges |
| `frontend/src/components/lab/MoleculePreview.tsx` | SVG molecule renderer |
| `frontend/src/components/genetics/UploadZone.tsx` | Drag-and-drop file upload |
| `frontend/src/components/shared/HubLayout.tsx` | Shared hub layout wrapper |
| `frontend/src/components/shared/SkeletonLoader.tsx` | Animated loading skeleton |
| `frontend/src/components/shared/StatusBadge.tsx` | Color-coded status indicator |

### Frontend — Modified Files
| File | Change |
|:---|:---|
| `frontend/src/components/lab/LabDashboard.tsx` | Premium redesign: SVG preview, ADMET grid, skeleton loaders |
| `frontend/src/components/genetics/GeneticsDashboard.tsx` | Premium redesign: drag-drop upload, structured result cards |
| `frontend/src/components/studio/CreationStudio.tsx` | Premium redesign: recent topics, side-by-side preview |
| `frontend/capacitor.config.ts` | Add server config for API |

---

## Execution Order

### Sprint 1: Foundation + CORS (Week 1) — ~3 days
1. Add Capacitor origins to `main.py` + `config.py` CORS
2. Create `export_processor.py` + register in container
3. Update `multi_provider.py` models (`claude-airforce`)
4. Write CORS + export regression tests
5. Run `./run_regression.sh` — verify all ≤ 10s

### Sprint 2: UI Polish (Week 1-2) — ~5 days
1. Create shared components (`HubLayout`, `SkeletonLoader`, `StatusBadge`)
2. Redesign `LabDashboard.tsx` with SVG preview + ADMET grid
3. Redesign `GeneticsDashboard.tsx` with drag-drop + structured cards
4. Redesign `CreationStudio.tsx` with recent topics + progress bar
5. Run `cd frontend && npm run build` — verify no type errors

### Sprint 3: Integration + Mobile (Week 2-3) — ~3 days
1. Test Capacitor build: `cd frontend && npx cap sync`
2. Test on iOS simulator + Android emulator
3. Update `capacitor.config.ts` with server config
4. End-to-end smoke test all 3 hubs
5. Deploy backend + frontend
