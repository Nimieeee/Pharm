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

This artifact will be read at the start of every Claude session to maintain context of the Benchside codebase.