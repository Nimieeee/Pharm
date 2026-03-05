# CLAUDE MEMORY ARTIFACT

This file serves as Claude's permanent memory of the Benchside codebase architecture, deployment details, and technical stack.

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
- **Key Services**:
  - **Deep Research Service**: 4-node pipeline (Planner → Researcher → Reviewer → Writer).
  - **Multi-Provider Router**: Intelligent load-balancing between NVIDIA, Groq, Pollinations, and Mistral.
  - **Enhanced RAG**: Multi-format document ingestion (PDF, DOCX, PPTX, XLSX, CSV, SDF).
  - **Research Tools**: Specialized integration with PubMed (API Key), Semantic Scholar, and Web Search (Tavily/Serper).

### Key Integration Points
- **Frontend → Backend**: API calls and SSE streams for real-time progress.
- **Deep Research Flow**: Sequential planning → Parallel searching → Recursive review → 25k token synthesis.
- **UI Non-Blocking**: Chat Input scoped to conversation ID, allowing multiple active streams.

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
- **PM2 Service**: `benchside-api` (Port 7860)

#### Deployment Workflow
1. **Sync files using rsync**
   ```bash
   rsync -avz -e "ssh -i ~/.ssh/lightsail_key" --exclude '.venv' --exclude '__pycache__' --exclude '.git' --exclude 'node_modules' --exclude '.next' --exclude '.env' backend/ ubuntu@15.237.208.231:/var/www/benchside-backend/backend/
   ```

2. **Restart the backend service via PM2**
   ```bash
   ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 restart benchside-api"
   ```

3. **Verify the service is online**
   ```bash
   ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 logs benchside-api --lines 20 --nostream"
   ```

4. **Deploy the frontend changes to GitHub (triggers Vercel)**
   *Note: Always verify the frontend build locally before pushing.*
   ```bash
   cd frontend && npm run build && cd .. && git add . && git commit -m "chore(rebrand): update to benchside" && git push origin master
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

**Specific Test Files**:
```bash
python backend/tests/verify_rag_e2e.py
python /tmp/test_pubmed_standalone.py # Validates PubMed API key & results yield
```

## CONTEXT

### Current State
1. **Recent Focus**: Deep Research 2.0 (High-Density Academic Synthesis)
2. **Key Capabilities**:
   - **25k Token Reports**: Elite mode writer for massive academic reviews.
   - **PubMed Hardening**: API key integration for 10 req/s and 50 papers/query.
   - **Hybrid Routing**: Tier 1 (Gemini) vs Tier 2 (Kimi) fallback logic.
   - **UI Decoupling**: Non-blocking research allowing parallel chat interaction.
3. **Recent Fixes**:
   - Resolved 20% progress stall by optimizing API timeouts and key usage.
   - Fixed `isLoading` race condition on conversation switch.
   - Implemented programmatically appended APA citations.

### Technical Stack Summary

**Frontend**:
- Next.js 14, TypeScript, Tailwind CSS
- Framer Motion for animations
- Lucide React for iconography
- Custom Streaming state management

**Backend**:
- FastAPI, PostgreSQL (Supabase)
- Multi-provider AI Strategy (Primary: NVIDIA/Groq/Pollinations)
- Molecular Pathway Mapping & Clinical Trial Binding logic
- Mistral-Embed for vectorization

### Performance Considerations
- **Search Latency**: PubMed timeout optimized to 15s to prevent research stalls.
- **Output Capacity**: Internal max_tokens expanded to 25k for detailed reports.
- **Provider Redundancy**: Automatic failover to Groq/Kimi if Pollinations/Gemini fails.

## REGRESSION PREVENTION & SYSTEMATIC DEBUGGING

To maintain the integrity of the Benchside codebase, strict adherence to these principles is required:

### 1. The Iron Law of Debugging
**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**
Symptom fixes are a failure. Never apply a patch without fully understanding *why* the bug occurred at the source.

### 2. The Four Phases of Systematic Debugging
1. **Root Cause**: Read errors fully, reproduce consistently, check recent changes, and gather evidence at component boundaries. Trace data flow backward.
2. **Pattern Analysis**: Find working examples in the codebase. Compare broken vs. working code. Understand dependencies.
3. **Hypothesis**: Form a single, specific hypothesis ("I think X is the root cause because Y"). Test minimally.
4. **Implementation**: Create a failing test case *first*. Implement a single targeted fix. Verify. If 3+ fixes fail, **STOP** and question the architecture instead of continuing to patch.

### 3. Core Regression Prevention Strategies
- **Test-Driven Development (TDD)**: Write tests before code to establish expected behavior and prevent regressions.
- **Automate Testing**: Implement automated tests (unit, integration, UI) that run frequently.
- **CI/CD Integration**: Automatically validate code changes in the pipeline before deployment.
- **Manage Technical Debt**: Regularly refactor code to improve maintainability.
- **Feature Flags**: Safely deploy, test, and toggle features to mitigate failure impact.
- **Analyze Escaped Bugs**: Treat bugs that reach production as learning opportunities to improve test coverage.

### 4. Core Workflows & Output Standards
- **Brainstorming First**: Before jumping into any creative work (new features, UI components, major refactors), ALWAYS pause to brainstorm. Ask clarifying questions about user intent, outline the architecture, and propose a design before writing implementation code.
- **Test-Driven Development**: When implementing any logical feature or bug fix, you MUST write the test that defines success *first*. Implement the code only until the test passes. Correctness first, naive implementation second, optimization third.
- **Assumption Surfacing**: Explicitly state assumptions ("ASSUMPTIONS I'M MAKING: 1...") before implementing non-trivial logic.
- **Confusion Management**: When encountering inconsistencies or conflicting requirements, STOP. Name the confusion and ask for clarification. Do not guess.
- **Simplicity Enforcement**: Resist overcomplication. Prefer the boring, obvious solution. 
- **Scope Discipline**: Touch only what is requested. Overly ambitious refactoring introduces regressions.

This artifact will be read at the start of every Claude session to maintain context of the Benchside codebase.