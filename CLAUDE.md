# CLAUDE MEMORY ARTIFACT

This file serves as Claude's permanent memory of the PharmGPT codebase architecture, deployment details, and technical stack.

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
  - AI chat endpoints (Mistral, Groq APIs)
  - Document processing (PDF, PPTX, DOCX, images)
  - RAG (Retrieval-Augmented Generation) pipeline
  - User management and authentication
  - Research tools and transcription services

### Key Integration Points
- **Frontend → Backend**: API calls to `NEXT_PUBLIC_API_URL` (currently `https://35-181-4-139.sslip.io`)
- **Authentication**: JWT tokens managed by Supabase
- **Real-time Features**: WebSocket-like streaming for chat responses
- **Document Processing**: File upload → backend processing → vector embeddings → RAG retrieval

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
- **Deployment Commands**:
  ```bash
  # Sync backend to VPS (excluding node_modules, .git, etc.)
  rsync -avz -e "ssh -i ~/.ssh/lightsail_key -o StrictHostKeyChecking=no" --exclude 'node_modules' --exclude '.git' --exclude '__pycache__' --exclude '.env' --exclude 'logs/' backend/ ubuntu@15.237.208.231:/var/www/pharmgpt-backend/backend/

  # Restart backend service
  ssh -i ~/.ssh/lightsail_key -o StrictHostKeyChecking=no ubuntu@15.237.208.231 "pm2 restart pharmgpt-backend"
  ```
- **Ports**:
  - Backend API: 8000
- **Environment Variables**:
  - `SUPABASE_URL`: Supabase project URL (hosted separately, not on VPS)
  - `SUPABASE_ANON_KEY`: Supabase anonymous key
  - `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key
  - `SECRET_KEY`: JWT secret key
  - `MISTRAL_API_KEY`: Mistral AI API key
  - `GROQ_API_KEY`: Groq API key
  - `TAVILY_API_KEY`: Tavily search API key
  - `SERP_API_KEY`: SERP API key
  - `ADMIN_EMAIL`: Admin email
  - `ADMIN_PASSWORD`: Admin password

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
uvicorn main:app --reload
# Runs on http://localhost:8000
```

### Build Commands

**Frontend Build**:
```bash
cd frontend
npm run build
```

**Backend Build** (creates virtual environment and installs dependencies):
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Test Commands

**Frontend Tests** (Vitest):
```bash
cd frontend
npm test
```

**Backend Tests** (Pytest):
```bash
cd backend
pytest
```

**Specific Test Files**:
```bash
# Example backend tests
python backend/tests/verify_rag_e2e.py
python backend/tests/verify_pdf_speed.py
```

### Database Operations

**Run Migrations**:
```bash
# Either through Supabase Studio SQL editor or via Python script
python backend/scripts/run_migrations.py
```

**Check Database**:
```bash
python backend/check_conversations.py
python backend/check_db_dims.py
```

## CONTEXT

### Current State
Based on the history file analysis:

1. **Recent Focus**: Optimization of RAG (Retrieval-Augmented Generation) pipeline performance
2. **Key Challenges**:
   - Document upload and processing bottlenecks
   - Mistral embeddings API rate limits (1 req/s)
   - Batch processing implementation for efficiency
3. **Recent Changes**:
   - Implemented batched RAG processing
   - Added rate limiting utilities
   - Optimized PDF and document processing
   - Enhanced error handling and logging

### Technical Stack Summary

**Frontend**:
- Next.js 14, React 18, TypeScript
- Tailwind CSS for styling
- SWR for data fetching
- Mermaid for diagrams
- LangChain for AI integrations

**Backend**:
- FastAPI with Uvicorn
- PostgreSQL via Supabase
- LangChain, MistralAI, Groq APIs
- Sentence Transformers for embeddings
- RDKit for chemical structure parsing
- APScheduler for background tasks

**AI/ML Stack**:
- Mistral AI models (via API)
- Groq API for fast inference
- Tavily/SERP for web search
- Local embeddings via Sentence Transformers
- Document processing (PDF, PPTX, DOCX, images with OCR)

### Deployment Workflow

1. **Frontend**: Built and deployed to Vercel from GitHub repository
2. **Backend**:
   - Developed locally
   - Synced to AWS Lightsail VPS via rsync
   - Managed by PM2 process manager
3. **Database**: Cloud-hosted Supabase (separate service, not on VPS)

### Performance Considerations

- RAG pipeline optimization has been a major focus
- Batch processing implemented to handle rate limits
- Local embeddings available as fallback
- Caching mechanisms in place for frequent queries

This artifact will be read at the start of every Claude session to maintain context and understanding of the PharmGPT codebase.