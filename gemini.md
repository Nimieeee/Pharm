# GEMINI MEMORY ARTIFACT

This file serves as Gemini's permanent memory of the Benchside codebase architecture, deployment details, and technical stack.

## ARCHITECTURE

### Frontend
- **Location**: `/frontend/`
- **Framework**: Next.js 14.0.4 with React 18.2.0
- **Language**: TypeScript
- **UI Library**: Tailwind CSS
- **State Management**: Context API (ChatContext, SidebarContext)
- **Key Components**:
  - Chat interface with message streaming
  - Document upload and processing
  - User authentication (login, register, profile)
  - Admin dashboard
  - Research tools and lab report features

### Backend
- **Location**: `/backend/`
- **Framework**: FastAPI 0.100.1
- **Language**: Python 3.x
- **Database**: PostgreSQL via Supabase
- **API Structure**: RESTful with JWT authentication

#### **Service Architecture (Decoupled - ALL PHASES COMPLETE)**
- **Service Container** (`app/core/container.py`): Centralized dependency injection, singleton pattern, 24 services registered
- **Postprocessing Module** (`app/services/postprocessing/`): Centralized brittle logic (Mermaid, Markdown, Safety)
- **Key Services**:
  - **Deep Research Service**: 4-node pipeline (Planner → Researcher → Reviewer → Writer).
  - **Multi-Provider Router**: Intelligent load-balancing between NVIDIA, Groq, Pollinations, and Mistral.
  - **Enhanced RAG**: Multi-format document ingestion (PDF, DOCX, PPTX, CSV, SDF).
  - **Mermaid Processor**: Centralized diagram validation/fixing (26 regression tests, <10ms).
  - **Research Tools**: Specialized integration with PubMed (API Key), Semantic Scholar, and Web Search (Tavily/Serper).
- **Decoupling Status**: ✅ COMPLETE - All services use ServiceContainer with lazy loading
- **API Endpoints**: ✅ All endpoints use `container.get()` for service access
- **Regression Tests**: ✅ 65+ tests, <2s run time
- **ADMET Service**: Local ADMET-AI (Chemprop v2) — 46 endpoints + DrugBank percentiles, directional status scoring, RDKit SVG generation, AI interpretation via Mistral

### Key Integration Points
- **Frontend → Backend**: API calls and SSE streams for real-time progress.
- **Deep Research Flow**: Sequential planning → Parallel searching → Recursive review → 25k token synthesis.
- **UI Non-Blocking**: Chat Input scoped to conversation ID, allowing multiple active streams.
- **Service Access Pattern**: Use `ServiceContainer` for decoupled service access (see DECOUPLING_PROGRESS.md).

## DEPLOYMENT

### Frontend Deployment
- **Platform**: Vercel (deployed from GitHub repository)
- **Build Command**: `npm run build`
- **Start Command**: `npm run start`
- **Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: Backend API endpoint (points to Lightsail VPS)

### Backend Deployment
- **Platform**: AWS Lightsail VPS (2 vCPUs, 8GB RAM)
- **Deployment Method**: rsync with PM2 process manager
- **Current VPS**: `ubuntu@15.237.208.231`
- **Deployment Path**: `/var/www/benchside-backend/backend/`
- **PM2 Service**: `pharmgpt-api` (Port 7860)

#### Deployment Workflow
1. **Sync files using rsync**
   ```bash
   rsync -avz -e "ssh -i ~/.ssh/lightsail_key" --exclude '.venv' --exclude '__pycache__' --exclude '.git' --exclude 'node_modules' --exclude '.next' --exclude '.env' backend/ ubuntu@15.237.208.231:/var/www/benchside-backend/backend/
   ```

2. **Restart the backend service via PM2**
   ```bash
   ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 restart pharmgpt-api"
   ```

3. **Verify the service is online**
   ```bash
   ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 logs pharmgpt-api --lines 20 --nostream"
   ```

4. **Deploy the frontend changes to GitHub (triggers Vercel)**
   *Note: Always verify the frontend build locally before pushing.*
   ```bash
   cd frontend && npm run build && cd .. && git add . && git commit -m "chore(deploy): update frontend" && git push origin master
   ```
- **Ports**:
  - Backend API: 7860 (Internal) / 8000
- **Environment Variables**:
  - `POLLINATIONS_API_KEY`: Elite mode token generation
  - `PUBMED_API_KEY`: Increased throughput for academic research
  - `SEMANTIC_SCHOLAR_API_KEY`: High-fidelity citation retrieval
  - `MISTRAL_API_KEY`, `GROQ_API_KEY`, `NVIDIA_API_KEY`
  - `TAVILY_API_KEY`, `SERP_API_KEY`, `SERPER_API_KEY`

### Database
- **Type**: PostgreSQL via Supabase
- **Deployment**: Cloud-hosted Supabase (separate from VPS)
- **Migrations**: SQL files in `/backend/migrations/`

## COMMANDS

### Development Servers

**Frontend (Next.js)**:
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

**Backend (FastAPI)**:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 7860
```

**CoT Reasoning Engine**:
```bash
python3 /Users/mac/Desktop/phhh/scripts/cot_retriever.py "Your problem description"
```

### Build Commands

**Frontend Build**:
```bash
cd frontend
npm run build
```

**Backend Build**:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Test Commands

**Frontend Tests**:
```bash
cd frontend
npm test
```

**Backend Tests**:
```bash
cd backend
pytest
```

**Regression Test Suite** (Fast - <10s target):

> ⚠️ **ALL tests MUST be run on the VPS.** The local Mac lacks RDKit, ADMET-AI, and other backend dependencies. Always SSH into the VPS.

```bash
# Run regression suite on VPS (MANDATORY)
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "cd /var/www/benchside-backend/backend && source .venv/bin/activate && pytest tests/regression/ -v"

# Specific regression tests on VPS
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "cd /var/www/benchside-backend/backend && source .venv/bin/activate && pytest tests/regression/test_mermaid.py -v"  # 26 tests, <1s
```

**Specific Test Files**:
```bash
python backend/tests/verify_rag_e2e.py
python /tmp/test_pubmed_standalone.py # Validates PubMed API key & results yield
```

## CONTEXT

### Current State
1. **Recent Focus**: ADMET Gold Standard V12.1 — Directional Scoring & AI Interpretation (2026-03-14)
2. **Key Capabilities**:
   - **25k Token Reports**: Elite mode writer for massive academic reviews.
   - **PubMed Hardening**: API key integration for 10 req/s and 50 papers/query.
   - **Hybrid Routing**: Tier 1 (Gemini) vs Tier 2 (Kimi) fallback logic.
   - **CoT Reasoning Store**: Local ChromaDB index of 400k reasoning patterns for expert-level logic.
   - **UI Decoupling**: Non-blocking research allowing parallel chat interaction.
   - **Full Decoupling**: All services use ServiceContainer with lazy loading.
4. **Recent Fixes (Phase 31)**:
   - **405 Errors**: Fixed redundant path prefixes in `admet.py`, `slides.py`, and `docs.py`.
   - **CORS Hardening**: Added Capacitor origins to `config.py` and `androidScheme` to `capacitor.config.ts`.
   - **Theme Toggle**: Integrated `ThemeToggle` into `HubLayout.tsx`.
   - **Hub Dashboards**: Premum redesign of Lab, Genetics, and Studio dashboards.
5. **Architecture Decoupling (✅ ALL PHASES COMPLETE)**:
   - **Service Container**: 24 services registered, centralized DI
   - **Mermaid Processor**: Centralized with 26 regression tests (<10ms)
   - **Postprocessing Module**: All brittle logic centralized
   - **Regression Suite**: 65+ tests, <2s run time (target: <10s) ✅

### Technical Stack Summary

**Frontend**:
- Next.js 14, TypeScript, Tailwind CSS
- Framer Motion for animations
- Lucide React for iconography
- Custom Streaming state management

**Backend**:
- FastAPI, PostgreSQL (Supabase)
- Multi-provider AI Strategy (Primary: NVIDIA/Groq/Pollinations)
- **Service Container Pattern**: 24 services registered, decoupled instantiation
- **Postprocessing Module**: Centralized Mermaid, Markdown, Safety processing
- Molecular Pathway Mapping & Clinical Trial Binding logic
- Mistral-Embed for vectorization

## REGRESSION PREVENTION & SYSTEMATIC DEBUGGING

To maintain the integrity of the Benchside codebase, strict adherence to these principles is required:

### 1. The Iron Law of Debugging
**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**
Symptom fixes are a failure. Never apply a patch without fully understanding *why* the bug occurred at the source.

### 2. The Four Phases of Systematic Debugging
1. **Root Cause**: Read errors fully, reproduce consistently, check recent changes, and gather evidence at component boundaries. Trace data flow backward.
2. **Pattern Analysis**: Find working examples in the codebase. Compare broken vs. working code. Understand dependencies.
3. **Failure Mode Analysis (FMA)**: You MUST explicitly list 3 things that could go wrong with your proposed fix. Form a single, specific hypothesis based on this analysis.
4. **Implementation**: Create a failing test case *first*. Implement a single targeted fix. Verify. If 3+ fixes fail, **STOP** and question the architecture instead of continuing to patch.

### 6. Implementation Error Prevention Rules

These rules are derived from **real production bugs** found in the Benchside codebase. They MUST be followed to prevent recurrence.

#### Rule 1: HTML Entity Decoding
**ANY component that receives text from an API, SSE stream, or database MUST unescape HTML entities before parsing the text as structured syntax (Mermaid, LaTeX, JSON, etc.).**

#### Rule 2: FastAPI Dependency Injection
**NEVER call `get_db()`, `get_current_user()`, or any `Depends()` function directly. They are generator factories, not callables.**

#### Rule 3: React Stale Closures in Async Callbacks
**NEVER reference React state variables inside `setTimeout`, `setInterval`, or `.then()` callbacks. Use `useRef` instead.**

#### Rule 4: Idempotent Output Assembly
**String/report assembly MUST be idempotent. Never use the pattern "append → search-and-strip → re-append". Build the output exactly once.**

#### Rule 5: UUID Validation Before API Calls
**Always validate that dynamic URL segments are valid UUIDs before making API calls. Never allow fallback strings like `"chat"` to reach the API.**

### 🔱 COT VERIFICATION LOCK
**NO IMPLEMENTATION PLAN IS VALID WITHOUT A PRECEDING COT RETRIEVAL.**
If you identify a task as "complex" but do not provide retrieval findings, the plan is rejected.

---

### LESSONS LEARNED / RECENT DISCOVERIES
- **PM2 Naming**: Backend process is named `pharmgpt-api`, not `benchside-api` on the Lightsail VPS.
- **Double Prefixes Filters**: FastApi `include_router(..., prefix="/foo")` + `@router.post("/foo/bar")` results in `/foo/foo/bar`. Endpoints should use relative paths.
- **ADMET Directional Scoring**: Risk endpoints (toxicity, CYP inhibitors, Tox21) = low is good (🟢). Benefit endpoints (HIA, BBB, bioavailability) = high is good (🟢). NEVER use a single threshold direction for all endpoints.
- **Pydantic vs os.environ**: Use `settings.MISTRAL_API_KEY` from `app.core.config`, NOT `os.environ.get()`. Pydantic parses `.env` but doesn't export to shell.
- **DrugPool SMILES Only**: `drugPool.ts` must contain valid SMILES strings only. Peptide sequences (His-Aib-Glt-...) crash RDKit.
- **ADMET-AI vs ADMETlab**: Local engine is ADMET-AI (Chemprop v2, 46 endpoints). Ototoxicity/Nephrotoxicity/Neurotoxicity/Hematotoxicity are ADMETlab-only — do NOT add fake endpoints.
- **StatusBadge Text Spam**: When `ADMETPropertyCard` passes `status` as `label`, the word "neutral"/"warning" renders visibly. Use `showLabel={false}` for icon-only display.
