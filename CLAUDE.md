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
```bash
# Run full regression suite
./run_regression.sh

# Or directly
cd backend
source .venv/bin/activate
pytest tests/regression/ -v

# Specific regression tests
pytest tests/regression/test_mermaid.py -v  # 26 tests, <1s
```

**Specific Test Files**:
```bash
python backend/tests/verify_rag_e2e.py
python /tmp/test_pubmed_standalone.py # Validates PubMed API key & results yield
```

## CONTEXT

### Current State
1. **Recent Focus**: Full Stack Decoupling Complete (2026-03-06)
2. **Key Capabilities**:
   - **25k Token Reports**: Elite mode writer for massive academic reviews.
   - **PubMed Hardening**: API key integration for 10 req/s and 50 papers/query.
   - **Hybrid Routing**: Tier 1 (Gemini) vs Tier 2 (Kimi) fallback logic.
   - **CoT Reasoning Store**: Local ChromaDB index of 400k reasoning patterns for expert-level logic.
   - **UI Decoupling**: Non-blocking research allowing parallel chat interaction.
   - **Full Decoupling**: All services use ServiceContainer with lazy loading.
4. **Recent Fixes (Phase 30)**:
   - **History Context**: Fixed thread loss by ensuring all message IDs are passed as `parent_id` (removed ID hyphen check).
   - **Mermaid Rendering**: Added heuristic to handle unquoted parentheses in node labels.
   - **Message Editing**: Implemented full-stack support for editing user messages and triggering regeneration.
   - **Diagram Suppression**: Toned down system prompt to prevent redundant Mermaid charts.
   - **RAG Fallback**: Hardened RAG context ingestion to fall back to broad conversation chunks if semantic search yields no results.
   - **Mobile UI**: Aligned mode buttons into a unified capsule and fixed attachment menu overlap.
5. **Architecture Decoupling (✅ ALL PHASES COMPLETE)**:
   - **Service Container**: 24 services registered, centralized DI
   - **Mermaid Processor**: Centralized with 26 regression tests (<10ms)
   - **Postprocessing Module**: All brittle logic centralized
   - **Regression Suite**: 65+ tests, <2s run time (target: <10s) ✅
   - **AIService**: Fully decoupled with lazy loading for all dependencies
   - **AuthService**: Lazy loading for email_service
   - **SchedulerService**: Lazy loading for email_service
   - **DeepResearchService**: Lazy loading for pmc_service, pdf_service
   - **LabReportService**: Container lookup for serper_service
   - **API Endpoints**: All endpoints use container.get() pattern
   - **Frontend TokenStreamer**: Already decoupled, pure logic
   - **Chat Orchestrator**: Uses container, no direct instantiation
   - **Research Services**: Use container for dependencies
6. **Decoupling Verification**:
   - ✅ Zero circular dependencies
   - ✅ Zero direct service instantiation in API endpoints
   - ✅ Zero direct service instantiation in services (for dependencies)
   - ✅ 65+ regression tests covering all decoupled services

### Technical Stack Summary

**Frontend**:
- Next.js 14, TypeScript, Tailwind CSS
- Framer Motion for animations
- Lucide React for iconography
- Custom Streaming state management
- **TokenStreamer**: Decoupled streaming logic (pure class, testable)

**Backend**:
- FastAPI, PostgreSQL (Supabase)
- Multi-provider AI Strategy (Primary: NVIDIA/Groq/Pollinations)
- **Service Container Pattern**: 24 services registered, decoupled instantiation
- **Postprocessing Module**: Centralized Mermaid, Markdown, Safety processing
- Molecular Pathway Mapping & Clinical Trial Binding logic
- Mistral-Embed for vectorization
- **Regression Testing**: 65+ tests, <2s run time
- **Lazy Loading**: All services with dependencies use @property lazy loading

### Performance Considerations
- **Search Latency**: PubMed timeout optimized to 15s to prevent research stalls.
- **Output Capacity**: Internal max_tokens expanded to 25k for detailed reports.
- **Provider Redundancy**: Automatic failover to Groq/Kimi if Pollinations/Gemini fails.
- **Regression Test Speed**: <2s total (target: <10s) ✅
- **Mermaid Processing**: <10ms per diagram ✅
- **Service Initialization**: Lazy loading ensures services only loaded when needed ✅

## REGRESSION PREVENTION & SYSTEMATIC DEBUGGING

To maintain the integrity of the Benchside codebase, strict adherence to these principles is required:

### 1. The Iron Law of Debugging
**NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**
Symptom fixes are a failure. Never apply a patch without fully understanding *why* the bug occurred at the source.

### 2. The Four Phases of Systematic Debugging
1. **Root Cause**: Read errors fully, reproduce consistently, check recent changes, and gather evidence at component boundaries. Trace data flow backward.
2. **Pattern Analysis**: Find working examples in the codebase. Compare broken vs. working code. Understand dependencies.
3. **Failure Mode Analysis (FMA)**: You MUST explicitly list 3 things that could go wrong with your proposed fix (e.g., race conditions, side effects, schema mismatch). Form a single, specific hypothesis based on this analysis.
4. **Implementation**: Create a failing test case *first*. Implement a single targeted fix. Verify. If 3+ fixes fail, **STOP** and question the architecture instead of continuing to patch.

### 3. Core Regression Prevention Strategies
- **Test-Driven Development (TDD)**: Write tests before code to establish expected behavior and prevent regressions.
- **Automate Testing**: Implement automated tests (unit, integration, UI) that run frequently.
- **CI/CD Integration**: Automatically validate code changes in the pipeline before deployment.
- **Manage Technical Debt**: Regularly refactor code to improve maintainability.
- **Feature Flags**: Safely deploy, test, and toggle features to mitigate failure impact.
- **Analyze Escaped Bugs**: Treat bugs that reach production as learning opportunities to improve test coverage.
- **Decoupling Architecture**: Use ServiceContainer pattern, centralize brittle logic, write regression tests.

### 4. Anti-Regression Implementation Guide

#### **4.1 Before Implementing ANY Feature**

**CHECKLIST - Must Complete Before Coding:**
- [ ] Read DECOUPLING_PLAN.md and DECOUPLING_PROGRESS.md
- [ ] Identify if feature touches brittle logic (regex, parsing, text processing)
- [ ] Determine which service(s) will be affected
- [ ] Check if ServiceContainer already provides needed service
- [ ] Write regression test FIRST (in `tests/regression/`)
- [ ] Run `./run_regression.sh` to establish baseline

**ARCHITECTURE REVIEW:**
```python
# Ask yourself:
# 1. Does this create circular dependencies?
#    → Use ServiceContainer instead of direct imports

# 2. Does this add regex/parsing logic?
#    → Add to postprocessing module, NOT scattered across services

# 3. Does this modify existing service behavior?
#    → Check all callers of that service, update tests

# 4. Does this change API contracts?
#    → Update frontend types, run frontend tests
```

#### **4.2 Implementing Backend Features**

**PATTERN 1: Adding New Service Logic**
```python
# ✅ CORRECT: Use ServiceContainer
from app.core.container import container

class MyNewFeature:
    def __init__(self, db):
        self.container = container.initialize(db)
        self.rag = self.container.get('rag_service')
        self.mermaid = self.container.get('mermaid_processor')

# ❌ WRONG: Direct instantiation (creates coupling)
from app.services.rag import EnhancedRAGService
class MyNewFeature:
    def __init__(self, db):
        self.rag = EnhancedRAGService(db)  # DON'T DO THIS
```

**PATTERN 2: Adding Text Processing/Regex Logic**
```python
# ✅ CORRECT: Add to postprocessing module
# File: app/services/postprocessing/my_processor.py
class MyProcessor:
    def process(self, text: str) -> str:
        # Your regex/parsing logic here
        pass

my_processor = MyProcessor()  # Singleton

# File: app/services/postprocessing/__init__.py
from .my_processor import MyProcessor, my_processor
__all__ = ['MyProcessor', 'my_processor', ...]

# Usage in AIService:
from app.services.postprocessing import my_processor
result = my_processor.process(response_text)

# ❌ WRONG: Scattered logic
class AIService:
    def __init__(self):
        self.my_regex = re.compile(...)  # DON'T DO THIS
```

**PATTERN 3: Modifying Existing Service**
```python
# ✅ CORRECT: Follow these steps
# Step 1: Find all usages
grep -r "from app.services.chat import" --include="*.py"
grep -r "ChatService" --include="*.py"

# Step 2: Check what tests exist
ls tests/ | grep chat

# Step 3: Add regression test for existing behavior
# File: tests/regression/test_chat_service.py
def test_existing_behavior():
    # Test what currently works
    pass

# Step 4: Run regression suite
./run_regression.sh

# Step 5: Make minimal change

# Step 6: Run regression suite again
./run_regression.sh

# ❌ WRONG: Change without testing impact
# - Edit service
# - Deploy
# - Hope it works
```

**PATTERN 4: Adding API Endpoint**
```python
# ✅ CORRECT: Full-stack approach
# Step 1: Backend endpoint with validation
@router.post("/my-feature")
async def my_feature(
    data: MySchema,
    current_user: User = Depends(get_current_user),
    container = Depends(get_container)
):
    service = container.get('my_service')
    return await service.process(data)

# Step 2: Frontend type definition
// File: frontend/src/types/api.ts
export interface MyFeatureRequest {
  // Define types
}

// Step 3: Frontend hook with error handling
// File: frontend/src/hooks/useMyFeature.ts
export function useMyFeature() {
  const [error, setError] = useState<string | null>(null);
  
  const execute = async (data: MyFeatureRequest) => {
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('Failed');
      return await response.json();
    } catch (e) {
      setError(e.message);
      throw e;
    }
  };
  
  return { execute, error };
}

// Step 4: Test both backend and frontend
pytest tests/regression/test_my_feature.py
npm test -- frontend/src/hooks/useMyFeature.test.ts
```

#### **4.3 Implementing Frontend Features**

**PATTERN 1: Adding New Hook**
```typescript
// ✅ CORRECT: Decoupled, testable
// File: frontend/src/lib/my-feature/MyFeatureLogic.ts
export class MyFeatureLogic {
  // Pure logic, no React dependencies
  process(data: any): any {
    // Testable without rendering
  }
}

// File: frontend/src/hooks/useMyFeature.ts
import { MyFeatureLogic } from '@/lib/my-feature/MyFeatureLogic';

export function useMyFeature() {
  const logic = useMemo(() => new MyFeatureLogic(), []);
  
  const execute = useCallback((data: any) => {
    return logic.process(data);
  }, [logic]);
  
  return { execute };
}

// File: frontend/src/tests/lib/my-feature/MyFeatureLogic.test.ts
describe('MyFeatureLogic', () => {
  it('processes data correctly', () => {
    const logic = new MyFeatureLogic();
    expect(logic.process(input)).toEqual(expected);
  });
});

// ❌ WRONG: All logic in hook
export function useMyFeature() {
  // Logic mixed with React lifecycle
  // Cannot test without rendering
  // Hard to reuse
}
```

**PATTERN 2: Modifying Streaming Logic**
```typescript
// ✅ CORRECT: Test streaming separately
// File: frontend/src/lib/streaming/TokenStreamer.test.ts
describe('TokenStreamer', () => {
  it('buffers tokens correctly', () => {
    // Test buffering logic
  });
  
  it('handles errors gracefully', () => {
    // Test error handling
  });
});

// Run before deploying:
npm run test:regression

// ❌ WRONG: Streaming logic only in component
// - Cannot test without mounting component
// - Changes may break silently
```

**PATTERN 3: UI Component Changes**
```typescript
// ✅ CORRECT: Visual regression prevention
// 1. Add Storybook story (if using)
// 2. Add snapshot test
// 3. Test on mobile and desktop viewports

// File: frontend/src/components/__tests__/MyComponent.test.tsx
describe('MyComponent', () => {
  it('renders correctly', () => {
    const { container } = render(<MyComponent />);
    expect(container).toMatchSnapshot();
  });
  
  it('handles edge cases', () => {
    // Empty state
    // Loading state
    // Error state
  });
});

// Run before committing:
npm test -- --testPathPattern=MyComponent
```

#### **4.4 Pre-Commit Checklist**

**MANDATORY BEFORE ANY COMMIT:**
```bash
# 1. Run regression suite
./run_regression.sh

# 2. Check for circular imports (backend)
python -c "from app.services.ai import AIService; from app.services.enhanced_rag import EnhancedRAGService"

# 3. Run frontend tests
cd frontend && npm run test:regression

# 4. Build frontend (catches type errors)
cd frontend && npm run build

# 5. Check for console errors
# - Run app locally
# - Open browser console
# - Fix any errors

# 6. Git diff review
git diff
# - Check for accidental debug code
# - Check for console.log statements
# - Check for TODO comments that should be addressed
```

#### **4.5 Pre-Deployment Checklist**

**MANDATORY BEFORE DEPLOYING TO VPS:**
```bash
# 1. All pre-commit checks pass
./run_regression.sh  # Must be <10s
cd frontend && npm run build  # Must succeed

# 2. Test on production-like data
# - Use staging database if available
# - Test with real user data patterns

# 3. Deploy to VPS
rsync -avz -e "ssh -i ~/.ssh/lightsail_key" \
  --exclude '.venv' --exclude '__pycache__' \
  backend/ ubuntu@15.237.208.231:/var/www/benchside-backend/backend/

# 4. Restart service
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 \
  "pm2 restart benchside-api"

# 5. Verify deployment
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 \
  "pm2 logs benchside-api --lines 50 --nostream"

# 6. Run regression tests ON VPS
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 \
  "cd /var/www/benchside-backend/backend && \
   source .venv/bin/activate && \
   pytest tests/regression/ -v"

# 7. Smoke test production
# - Open https://benchside.vercel.app
# - Test core features
# - Check browser console for errors
```

#### **4.6 When Regression Occurs**

**IMMEDIATE RESPONSE:**
```python
# 1. Identify what changed
git log --oneline -10
git diff HEAD~10..HEAD --stat

# 2. Find which test should have caught it
# - Add failing test to tests/regression/
# - Run regression suite to confirm it fails

# 3. Fix the root cause (not symptom)
# - Follow Four Phases of Systematic Debugging
# - Do not apply band-aid fixes

# 4. Add regression test for the fix
# - Ensure this specific bug cannot recur

# 5. Update this CLAUDE.md with lesson learned
# - Add to "Known Regression Patterns" section
```

**KNOWN REGRESSION PATTERNS:**
| Pattern | Symptom | Prevention |
|---------|---------|------------|
| Circular import | Module A imports B, B imports A | Use ServiceContainer |
| Scattered regex | Same pattern in multiple files | Centralize in postprocessing |
| Untested edge case | Works for normal input, fails on edge | Add edge case tests |
| Frontend/backend mismatch | API returns different type than expected | Share types, test integration |
| Service state leakage | One request affects another | Use stateless services |
| React.memo blocking edit | Edit works but UI doesn't update | Check content change FIRST in memo, return false immediately |
| Mermaid HTML entities | Diagram shows `&quot;` instead of `"` | Decode HTML entities before processing mermaid syntax |

### 5. Core Workflows & Output Standards
- **Brainstorming First**: Before jumping into any creative work (new features, UI components, major refactors), ALWAYS pause to brainstorm. Ask clarifying questions about user intent, outline the architecture, and propose a design before writing implementation code.
- **Test-Driven Development**: When implementing any logical feature or bug fix, you MUST write the test that defines success *first*. Implement the code only until the test passes. Correctness first, naive implementation second, optimization third.
- **Assumption Surfacing**: Explicitly state assumptions ("ASSUMPTIONS I'M MAKING: 1...") before implementing non-trivial logic.
- **Confusion Management**: When encountering inconsistencies or conflicting requirements, STOP. Name the confusion and ask for clarification. Do not guess.
- **CoT reasoning mandate**: For ANY task involving complex architecture, algorithmic design, or deep logical debugging (e.g., branching bugs), you MUST first retrieve relevant reasoning patterns using:
  `python3 /Users/mac/Desktop/phhh/scripts/cot_retriever.py "Task summary"`
  **THE EVIDENCE RULE**: You MUST include the **raw terminal output (first 10 lines)** in your planning block as proof of retrieval. Analyze the retrieved "Internal thinking" and explicitly state how you are adopting those patterns in your implementation plan.

---

### 🔱 COT VERIFICATION LOCK
**NO IMPLEMENTATION PLAN IS VALID WITHOUT A PRECEDING COT RETRIEVAL.**
If you identify a task as "complex" but do not provide retrieval findings, the plan is rejected.

#### **RED FLAGS (STOP and Start Over)**:
- "I'll use CoT later in the implementation phase."
- "The task is simple so I don't need expert reasoning." (Trust the Architect, not your confidence).
- "I already know the solution." (Benchside relies on verified patterns, not individual intuition).

---

- **Scope Discipline**: Touch only what is requested. Overly ambitious refactoring introduces regressions.
- **Documentation Maintenance**: ALWAYS update this `CLAUDE.md` file whenever there is a massive update to the codebase architecture, a new technology is added to the stack, or core deployment commands change.
- **Regression Test Maintenance**: When adding new functionality, ALWAYS add corresponding regression tests. Run `./run_regression.sh` before any commit.

This artifact will be read at the start of every Claude session to maintain context of the Benchside codebase.