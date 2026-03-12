 Key Sections:

1. Phase 1: UI Strategy - Hub-and-Spoke architecture with frontend
   components and handoff pattern
2. Phase 2: ADMET Integration - Backend service with ToxMCP patterns,
   dependencies, API endpoints
3. Phase 3: Local Inference - BitNet deployment, intelligent routing,
   concurrency queue
4. Phase 4: Testing Strategy - TDD-compliant regression tests for all
   components
5. Phase 5: Failure Mode Analysis - Risk tables with mitigations
6. Phase 6: Verification Plan - Pre-commit and deployment checklists
7. Phase 7: File Changes Summary - Complete list of new and modified
   files

  CLAUDE.md Compliance:

- ✅ ServiceContainer pattern for all services (lazy loading, singleton)
- ✅ Postprocessing module for text processing (prompt_processor,
  admet_processor, export_processor)
- ✅ TDD with regression tests defined before implementation
- ✅ Failure Mode Analysis included
- ✅ Execution order with 5 sprints over ~5 weeks

──────────────────────────────────────────────────────────────────────────
 Ready to code?

 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 Mega Plan: Benchside Scientific Platform Expansion

 Priority: UI Strategy (Frontend Hubs) → ADMET Integration → Local
 Inference
 RAM Strategy: Include ADMET dependencies in base VPS deployment
 Reference: CLAUDE.md (ServiceContainer, Postprocessing, TDD, FMA)

---

 Context

 This plan consolidates three implementation proposals into a unified,
 CLAUDE.md-compliant architecture:

1. UI Strategy - Hub-and-Spoke frontend with specialized dashboards
2. ADMET Integration - Drug discovery backend service with ToxMCP
   patterns
3. Local Inference - BitNet deployment with intelligent model routing

 The user has prioritized UI Strategy first, with ADMET dependencies
 included in base deployment.

---

 Phase 1: UI Strategy (Hub-and-Spoke Architecture)

 1.1 Architecture Overview

 ┌─────────────────────────────────────────────────────────────────┐
 │                        Frontend (Next.js)                        │
 ├─────────────────────────────────────────────────────────────────┤
 │                                                                   │
 │  ┌─────────────┐     ┌──────────────────────────────────────┐  │
 │  │   /chat     │────▶│ Handoff Component                     │  │
 │  │  (Spoke)    │     │  - "Open in Lab" → /lab?smiles=...    │  │
 │  │             │     │  - "View Genetics" → /genetics?rs=... │  │
 │  │             │     │  - "Edit in Studio" → /studio?doc=... │  │
 │  └─────────────┘     └──────────────────────────────────────┘  │
 │                                                                   │
 │  ┌─────────────────────────────────────────────────────────────┐│
 │  │                    SPECIALIZED HUBS                         ││
 │  ├─────────────────────────────────────────────────────────────┤│
 │  │  /lab        │ ADMET Viewer, PubMed Explorer, DDI Mapper   ││
 │  │  /genetics   │ PharmGx Visualizer, GWAS Context Mapper     ││
 │  │  /studio     │ Warp-Mode Outline, Side-by-Side Preview     ││
 │  └─────────────────────────────────────────────────────────────┘│
 └─────────────────────────────────────────────────────────────────┘
           │                              │
           ▼                              ▼
 ┌─────────────────────────────────────────────────────────────────┐
 │                      Backend (FastAPI)                           │
 ├─────────────────────────────────────────────────────────────────┤
 │  ServiceContainer (singleton)                                    │
 │  ├── admet_service (NEW)                                         │
 │  ├── router_service (NEW)                                        │
 │  ├── local_queue (NEW)                                           │
 │  ├── pubmed_service (MODIFY - add synthesis)                    │
 │  └── ... existing services                                       │
 │                                                                   │
 │  Postprocessing Module                                            │
 │  ├── mermaid_processor (existing)                                │
 │  ├── prompt_processor (NEW)                                      │
 │  ├── admet_processor (NEW)                                       │
 │  └── export_processor (NEW)                                      │
 └─────────────────────────────────────────────────────────────────┘

 1.2 Frontend Components

 Files to Create:

 ┌──────────────────────────────────────────────────────┬────────────┐
 │                         File                         │  Purpose   │
 ├──────────────────────────────────────────────────────┼────────────┤
 │ frontend/src/app/lab/page.tsx                        │ Lab Hub    │
 │                                                      │ route      │
 ├──────────────────────────────────────────────────────┼────────────┤
 │ frontend/src/app/genetics/page.tsx                   │ Genetics   │
 │                                                      │ Hub route  │
 ├──────────────────────────────────────────────────────┼────────────┤
 │                                                      │ Creation   │
 │ frontend/src/app/studio/page.tsx                     │ Studio     │
 │                                                      │ route      │
 ├──────────────────────────────────────────────────────┼────────────┤
 │                                                      │ ADMET      │
 │ frontend/src/components/lab/LabDashboard.tsx         │ Viewer,    │
 │                                                      │ DDI Mapper │
 ├──────────────────────────────────────────────────────┼────────────┤
 │ frontend/src/components/genetics/GeneticsDashboard.t │ PharmGx,   │
 │ sx                                                   │ GWAS visua │
 │                                                      │ lizers     │
 ├──────────────────────────────────────────────────────┼────────────┤
 │                                                      │ Warp-Mode  │
 │ frontend/src/components/studio/CreationStudio.tsx    │ Outline,   │
 │                                                      │ Preview    │
 ├──────────────────────────────────────────────────────┼────────────┤
 │                                                      │ Reusable   │
 │ frontend/src/components/chat/HandoffButton.tsx       │ handoff    │
 │                                                      │ component  │
 └──────────────────────────────────────────────────────┴────────────┘

 Files to Modify:

 ┌─────────────────────────────────────────────────┬──────────────────┐
 │                      File                       │      Change      │
 ├─────────────────────────────────────────────────┼──────────────────┤
 │                                                 │ Add handoff      │
 │ frontend/src/components/chat/MessageContent.tsx │ buttons to       │
 │                                                 │ scientific       │
 │                                                 │ messages         │
 └─────────────────────────────────────────────────┴──────────────────┘

 1.3 Backend Services

 NEW: backend/app/services/postprocessing/prompt_processor.py
 class PromptProcessor:
     """Prompt complexity analysis for intelligent routing."""

    COMPLEXITY_SIGNALS = [
         "review", "synthesize", "comprehensive", "compare and contrast",
         "systematic", "meta-analysis", "literature", "in-depth"
     ]

    PRIVACY_SIGNALS = [
         "patient", "genotype", "rs", "CYP", "HLA-", "allele",
         "my results", "my data", "confidential", "HIPAA"
     ]

    def score_complexity(self, prompt: str, token_count: int) -> float:
         """Return complexity score 0.0-1.0"""
         pass

    def detect_privacy(self, prompt: str) -> bool:
         """Detect if prompt contains sensitive data"""
         pass

 prompt_processor = PromptProcessor()  # Singleton

 NEW: backend/app/services/postprocessing/admet_processor.py
 class ADMETProcessor:
     """ADMET report formatting and export."""

    def format_svg_for_report(self, svg: str) -> str:
         """Clean and optimize SVG for markdown"""
         pass

    def format_csv_export(self, results: dict) -> str:
         """Convert ADMET results to CSV string"""
         pass

    def summarize_findings(self, admet_data: dict) -> str:
         """Generate clinical summary of ADMET results"""
         pass

 admet_processor = ADMETProcessor()  # Singleton

 NEW: backend/app/services/postprocessing/export_processor.py
 class ExportProcessor:
     """Generic export format processing."""

    def sanitize_svg(self, svg_content: str) -> str:
         """Remove potentially harmful SVG elements"""
         pass

    def format_csv(self, data: list, columns: list) -> str:
         """Format data as CSV with proper escaping"""
         pass

 export_processor = ExportProcessor()  # Singleton

 1.4 Service Container Registration

 MODIFY: backend/app/core/container.py

# Add new services to initialize():

 from app.services.admet_service import ADMETService
 from app.services.router_service import RouterService
 from app.services.local_queue import LocalInferenceQueue
 from app.services.postprocessing.prompt_processor import
 prompt_processor
 from app.services.postprocessing.admet_processor import admet_processor
 from app.services.postprocessing.export_processor import
 export_processor

# Register processors (stateless singletons)

 self._services['prompt_processor'] = prompt_processor
 self._services['admet_processor'] = admet_processor
 self._services['export_processor'] = export_processor

# Register services (with lazy loading for dependencies)

 self._services['admet_service'] = ADMETService(db)
 self._services['router_service'] = RouterService()
 self._services['local_queue'] = LocalInferenceQueue(max_queue_size=5)

---

 Phase 2: ADMET Integration

 2.1 Service Architecture

 NEW: backend/app/services/admet_service.py
 from app.core.container import container
 from app.services.postprocessing import admet_processor

 class ADMETService:
     """ADMET prediction service with ToxMCP robustness patterns."""

    def__init__(self, db: Client = None):
         self._db = db
         self._api_base = "https://admetlab3.scbdd.com"
         self._rate_limiter = RateLimiter(rps=5)  # 5 requests/sec

    @property
     def processor(self):
         """Lazy load ADMET processor from container"""
         if self._processor is None:
             self._processor = container.get('admet_processor')
         return self._processor

    async def wash_molecule(self, smiles: str) -> str:
         """Standardize SMILES via /api/washmol"""
         pass

    async def get_svg(self, smiles: str) -> str:
         """Generate molecule SVG via /api/molsvg"""
         pass

    async def predict_admet(self, smiles: str) -> dict:
         """Get 119 ADMET endpoints via /api/admet"""
         pass

    async def calculate_filters(self, smiles: str) -> dict:
         """PAINS, Lipinski, structural alerts via RDKit/Medchem"""
         pass

    async def generate_report(self, smiles: str) -> str:
         """Consolidated markdown report"""
         admet_data = await self.predict_admet(smiles)
         svg = await self.get_svg(smiles)
         return self.processor.format_report(admet_data, svg)

    def export_as_csv(self, results: dict) -> str:
         """CSV export via processor"""
         return self.processor.format_csv_export(results)

 2.2 Dependencies

 MODIFY: backend/requirements.txt

# Add ADMET dependencies

 PyTDC>=0.4.0          # Drug discovery datasets
 medchem>=0.2.0        # Medicinal chemistry
 datamol>=0.12.0        # Molecule manipulation
 deepchem>=2.7.0        # Deep learning for chemistry

 RAM Budget Impact:

- PyTDC: ~200MB
- medchem: ~50MB
- datamol: ~100MB (depends on RDKit, already installed)
- deepchem: ~300MB
- Total: ~650MB additional

 With BitNet 8B (~4.4GB) + OS + FastAPI + new deps:

- Total: ~6.0GB
- Buffer: ~2GB (acceptable)

 2.3 API Endpoints

 NEW: backend/app/api/v1/endpoints/admet.py
 from app.core.container import container
 from app.core.database import get_db

 def get_admet_service(db: Client = Depends(get_db)):
     if not container.is_initialized():
         container.initialize(db)
     return container.get('admet_service')

 @router.post("/admet/analyze")
 async def analyze_molecule(
     smiles: str,
     current_user: User = Depends(get_current_user),
     admet_service: ADMETService = Depends(get_admet_service)
 ):
     """Full ADMET analysis for a molecule."""
     return await admet_service.generate_report(smiles)

 @router.get("/admet/svg")
 async def get_molecule_svg(
     smiles: str,
     admet_service: ADMETService = Depends(get_admet_service)
 ):
     """Generate SVG for molecule structure."""
     return {"svg": await admet_service.get_svg(smiles)}

 @router.get("/admet/export")
 async def export_admet_csv(
     smiles: str,
     admet_service: ADMETService = Depends(get_admet_service)
 ):
     """Export ADMET results as CSV."""
     report = await admet_service.generate_report(smiles)
     return {"csv": admet_service.export_as_csv(report)}

---

 Phase 3: Local Inference (BitNet)

 3.1 Provider Integration

 MODIFY: backend/app/services/multi_provider.py
 class Provider(Enum):
     MISTRAL = "mistral"
     GROQ = "groq"
     NVIDIA = "nvidia"
     POLLINATIONS = "pollinations"
     LOCAL = "local"           # NEW

# Update MODE_PRIORITIES

 MODE_PRIORITIES = {
     "fast": [Provider.LOCAL, Provider.GROQ, Provider.POLLINATIONS],
     "detailed": [Provider.POLLINATIONS, Provider.LOCAL,
 Provider.NVIDIA],
     "deep_research": [Provider.POLLINATIONS, Provider.NVIDIA,
 Provider.GROQ],
     "deep_research_elite": [Provider.POLLINATIONS],
     "deep_research_single_pass": [Provider.GROQ],
 }

# LOCAL provider config (conditional)

 if os.getenv("LOCAL_MODEL_ENABLED", "false") == "true":
     self.providers[Provider.LOCAL] = ProviderConfig(
         name=Provider.LOCAL,
         api_key="not-needed",
         base_url=os.getenv("LOCAL_MODEL_URL",
 "http://127.0.0.1:8080/v1"),
         models={
             "fast": "bitnet-2b",
             "detailed": "bitnet-8b",
         },
         headers={"Content-Type": "application/json"},
         weight=1.0,
         rpm_limit=999,
     )

 3.2 Intelligent Router

 NEW: backend/app/services/router_service.py
 from app.services.postprocessing.prompt_processor import
 prompt_processor
 from app.core.container import container

 class RouterService:
     """Intelligent prompt routing based on complexity and privacy."""

    def__init__(self):
         self._queue = None  # Lazy loaded

    @property
     def queue(self):
         """Lazy load local inference queue"""
         if self._queue is None:
             self._queue = container.get('local_queue')
         return self._queue

    def route(self, prompt: str, token_count: int, mode: str) -> str:
         """
         Determine optimal provider based on mode + complexity.

    Returns: Provider name string
         """
         complexity = prompt_processor.score_complexity(prompt,
 token_count)
         is_private = prompt_processor.detect_privacy(prompt)
         queue_busy = self.queue.is_busy() if self.queue else True

    if mode == "fast":
             return self._route_fast(complexity, queue_busy)
         elif mode == "detailed":
             return self._route_detailed(complexity, is_private,
 queue_busy)
         elif mode in ("deep_research", "deep_research_elite"):
             return self._route_elite()

    def _route_fast(self, complexity: float, queue_busy: bool) -> str:
         if complexity < 0.3 and not queue_busy:
             return "local"      # BitNet 2B
         elif complexity < 0.6:
             return "groq"       # Groq 8B
         else:
             return "pollinations"  # Sonnet 4.6

    def _route_detailed(self, complexity: float, is_private: bool,
                         queue_busy: bool) -> str:
         if is_private:
             return "local"      # Privacy: never leaves VPS
         if complexity < 0.4 and not queue_busy:
             return "local"      # BitNet 8B
         return "pollinations"   # Sonnet 4.6

    def _route_elite(self) -> str:
         return "pollinations"    # Always Sonnet 4.6

 3.3 Concurrency Queue

 NEW: backend/app/services/local_queue.py
 import asyncio
 from fastapi import HTTPException

 class LocalInferenceQueue:
     """Serializes requests to local BitNet model."""

    def__init__(self, max_queue_size: int = 5):
         self._semaphore = asyncio.Semaphore(1)  # 1 concurrent request
         self._queue_size = 0
         self._max_queue = max_queue_size

    async def submit(self, request_fn):
         """Submit request to queue. Raises 503 if queue full."""
         if self._queue_size >= self._max_queue:
             raise HTTPException(503, "Local model queue full, try remote
  mode")

    self._queue_size += 1
         try:
             async with self._semaphore:
                 return await request_fn()
         finally:
             self._queue_size -= 1

    def is_busy(self) -> bool:
         """Check if queue has pending requests."""
         return self._queue_size > 0

    def queue_position(self) -> int:
         """Return current queue position."""
         return self._queue_size

---

 Phase 4: Testing Strategy (TDD Compliance)

 4.1 Regression Tests

 NEW: backend/tests/regression/test_admet_service.py
 import pytest
 from unittest.mock import Mock, patch, AsyncMock
 from app.services.admet_service import ADMETService
 from app.services.postprocessing.admet_processor import ADMETProcessor

 class TestADMETService:
     @pytest.fixture
     def service(self, mock_db):
         return ADMETService(mock_db)

    @pytest.fixture
     def processor(self):
         return ADMETProcessor()

    def test_service_initialization(self, service):
         """Test ADMET service initializes with lazy loading."""
         assert service._db is not None
         assert service._processor is None  # Lazy

    def test_processor_lazy_loads_from_container(self, service):
         """Test processor is lazy loaded from container."""
         processor = service.processor
         assert processor is not None
         assert service._processor is not None

    @pytest.mark.asyncio
     async def test_rate_limiting(self, service):
         """Test 5 rps rate limit is enforced."""
         # 6 rapid requests should trigger rate limit
         pass

    @pytest.mark.asyncio
     async def test_fallback_to_single_endpoint(self, service):
         """Test fallback from /api/admet to /api/single/admet."""
         pass

    @pytest.mark.asyncio
     async def test_wash_molecule(self, service):
         """Test molecule washing standardizes SMILES."""
         pass

    def test_csv_export(self, processor):
         """Test CSV formatting with proper escaping."""
         data = {"absorption": {"caco2": 0.85}}
         csv = processor.format_csv_export(data)
         assert "absorption" in csv.lower()

 class TestADMETProcessor:
     """Test ADMET postprocessing functions."""

    def test_svg_sanitization(self):
         """Test SVG sanitization removes harmful elements."""
         pass

    def test_report_formatting(self):
         """Test markdown report generation."""
         pass

 NEW: backend/tests/regression/test_router_service.py
 import pytest
 from app.services.router_service import RouterService
 from app.services.postprocessing.prompt_processor import PromptProcessor

 class TestRouterService:
     @pytest.fixture
     def router(self):
         return RouterService()

    @pytest.fixture
     def scorer(self):
         return PromptProcessor()

    def test_fast_mode_simple_routes_to_local(self, router):
         """Fast mode + simple prompt routes to LOCAL."""
         result = router.route("What is aspirin?", 10, "fast")
         assert result == "local"

    def test_fast_mode_complex_routes_to_groq(self, router):
         """Fast mode + complex prompt routes to GROQ."""
         result = router.route("Synthesize a comprehensive review...",
 500, "fast")
         assert result == "groq"

    def test_detailed_mode_privacy_routes_to_local(self, router):
         """Detailed mode + privacy signal routes to LOCAL."""
         result = router.route("My CYP2D6 genotype is *4/*4", 50,
 "detailed")
         assert result == "local"

    def test_detailed_mode_standard_routes_to_pollinations(self,
 router):
         """Detailed mode + standard prompt routes to POLLINATIONS."""
         result = router.route("Explain warfarin resistance", 100,
 "detailed")
         assert result == "pollinations"

    def test_elite_mode_always_pollinations(self, router):
         """Elite mode always routes to POLLINATIONS."""
         result = router.route("Any prompt", 10, "deep_research_elite")
         assert result == "pollinations"

 class TestPromptProcessor:
     """Test prompt complexity scoring."""

    def test_short_simple_prompt_low_score(self):
         """Short simple prompt gets low complexity score."""
         scorer = PromptProcessor()
         score = scorer.score_complexity("What is aspirin?", 10)
         assert score < 0.3

    def test_long_complex_prompt_high_score(self):
         """Long complex prompt gets high complexity score."""
         scorer = PromptProcessor()
         prompt = "Conduct a systematic review and meta-analysis
 comparing..."
         score = scorer.score_complexity(prompt, 2000)
         assert score > 0.4

    def test_privacy_detection(self):
         """Privacy signals are detected correctly."""
         scorer = PromptProcessor()
         assert scorer.detect_privacy("My CYP2D6 genotype is *4/*4")
         assert scorer.detect_privacy("Patient with HLA-B*57:01")
         assert not scorer.detect_privacy("What is pharmacogenomics?")

 NEW: backend/tests/regression/test_local_queue.py
 import pytest
 import asyncio
 from app.services.local_queue import LocalInferenceQueue

 class TestLocalInferenceQueue:
     @pytest.fixture
     def queue(self):
         return LocalInferenceQueue(max_queue_size=5)

    @pytest.mark.asyncio
     async def test_single_request_passes(self, queue):
         """Single request passes through immediately."""
         async def dummy_request():
             return "result"

    result = await queue.submit(dummy_request)
         assert result == "result"

    @pytest.mark.asyncio
     async def test_queue_full_raises_503(self, queue):
         """6th concurrent request raises HTTPException."""
         async def slow_request():
             await asyncio.sleep(10)
             return "result"

    # Fill queue
         tasks = [queue.submit(slow_request) for _ in range(5)]

    # 6th should fail
         with pytest.raises(Exception) as exc_info:
             await queue.submit(slow_request)
         assert exc_info.value.status_code == 503

    def test_is_busy_returns_correct_state(self, queue):
         """Queue correctly reports busy state."""
         assert not queue.is_busy()
         # After submit, should be busy
         # ...

 4.2 Frontend Tests

 NEW: frontend/src/components/lab/__tests__/LabDashboard.test.tsx
 describe('LabDashboard', () => {
   it('renders ADMET viewer with molecule data', () => {
     // Test ADMET grid rendering
   });

   it('handles handoff from Chat with SMILES parameter', () => {
     // Test URL param passing
   });

   it('exports ADMET data as CSV', () => {
     // Test export functionality
   });
 });

---

 Phase 5: Failure Mode Analysis

 5.1 UI Strategy Risks

 ┌────────────────┬────────────┬────────┬────────────────────────────┐
 │      Risk      │ Likelihood │ Impact │         Mitigation         │
 ├────────────────┼────────────┼────────┼────────────────────────────┤
 │ State loss on  │            │        │ Use URL params for small   │
 │ refresh        │ Medium     │ High   │ data, IndexedDB for large  │
 │                │            │        │ datasets                   │
 ├────────────────┼────────────┼────────┼────────────────────────────┤
 │ Cross-route    │            │        │ Scope React Context to     │
 │ state          │ Medium     │ Medium │ conversation ID            │
 │ pollution      │            │        │                            │
 ├────────────────┼────────────┼────────┼────────────────────────────┤
 │ Mobile         │            │        │ Test responsive on 375px   │
 │ collapse       │ Medium     │ High   │ viewport, add              │
 │ failure        │            │        │ mobile-specific tests      │
 ├────────────────┼────────────┼────────┼────────────────────────────┤
 │ Handoff button │            │        │ Validate SMILES/rs numbers │
 │  missing data  │ Low        │ High   │  before showing handoff    │
 │                │            │        │ button                     │
 └────────────────┴────────────┴────────┴────────────────────────────┘

 5.2 ADMET Integration Risks

 ┌──────────────┬───────────┬───────┬───────────────────────────────┐
 │     Risk     │ Likelihoo │ Impac │          Mitigation           │
 │              │     d     │   t   │                               │
 ├──────────────┼───────────┼───────┼───────────────────────────────┤
 │ ADMETlab API │ Medium    │ Mediu │ Exponential backoff, fallback │
 │  timeout     │           │ m     │  to single endpoint           │
 ├──────────────┼───────────┼───────┼───────────────────────────────┤
 │ Rate         │           │       │ Implement client-side queue,  │
 │ limiting (5  │ High      │ Low   │ show estimated wait           │
 │ rps)         │           │       │                               │
 ├──────────────┼───────────┼───────┼───────────────────────────────┤
 │ RDKit import │ Low       │ Mediu │ datamol already depends on    │
 │  bloat       │           │ m     │ RDKit, reuse                  │
 ├──────────────┼───────────┼───────┼───────────────────────────────┤
 │ SVG XSS vuln │ Low       │ High  │ Sanitize SVG in export_proces │
 │ erability    │           │       │ sor.sanitize_svg()            │
 ├──────────────┼───────────┼───────┼───────────────────────────────┤
 │ Dependency   │ Medium    │ Mediu │ Monitor VPS RAM, add health   │
 │ RAM impact   │           │ m     │ check                         │
 └──────────────┴───────────┴───────┴───────────────────────────────┘

 5.3 Local Inference Risks

 ┌──────────────────┬────────────┬────────┬──────────────────────────┐
 │       Risk       │ Likelihood │ Impact │        Mitigation        │
 ├──────────────────┼────────────┼────────┼──────────────────────────┤
 │                  │            │        │ 4-bit KV cache, RAM      │
 │ Model OOM on VPS │ Low        │ High   │ monitoring,              │
 │                  │            │        │ auto-fallback            │
 ├──────────────────┼────────────┼────────┼──────────────────────────┤
 │ CPU contention   │ Medium     │ Medium │ Semaphore queue,         │
 │ with FastAPI     │            │        │ --threads 2 cap          │
 ├──────────────────┼────────────┼────────┼──────────────────────────┤
 │ RoPE quality     │            │        │ Test on medical          │
 │ degradation at   │ Medium     │ Low    │ benchmark before deploy  │
 │ 8k               │            │        │                          │
 ├──────────────────┼────────────┼────────┼──────────────────────────┤
 │ Lightsail CPU    │ Medium     │ Medium │ Monitor CPU credits,     │
 │ throttling       │            │        │ consider 4 vCPU upgrade  │
 ├──────────────────┼────────────┼────────┼──────────────────────────┤
 │ bitnet.cpp       │            │        │ systemd auto-restart,    │
 │ instability      │ Low        │ Medium │ health check, remote     │
 │                  │            │        │ fallback                 │
 └──────────────────┴────────────┴────────┴──────────────────────────┘

---

 Phase 6: Verification Plan

 6.1 Pre-Commit Checklist

# Run regression suite (must be <10s)

 ./run_regression.sh

# Check for circular imports

 python -c "from app.services.admet_service import ADMETService; from
 app.services.router_service import RouterService"

# Run frontend tests

 cd frontend && npm run test:regression

# Build frontend (catches type errors)

 cd frontend && npm run build

# Git diff review

 git diff

 6.2 Deployment Verification

# Deploy backend

 rsync -avz -e "ssh -i ~/.ssh/lightsail_key" 
   --exclude '.venv' --exclude '__pycache__' 
   backend/ ubuntu@15.237.208.231:/var/www/benchside-backend/backend/

# Restart PM2

 ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "pm2 restart
 benchside-api"

# Verify BitNet (if enabled)

 ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 "curl -s
 http://127.0.0.1:8080/v1/models"

# Run regression tests ON VPS

 ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 
   "cd /var/www/benchside-backend/backend && 
    source .venv/bin/activate &&
    pytest tests/regression/ -v"

# Smoke test

# - Open /lab with ?smiles=CC(=O)Oc1ccccc1C(=O)O

# - Verify ADMET grid renders

# - Test CSV export

# - Open /chat, send "Analyze aspirin", click "Open in Lab"

---

 Phase 7: File Changes Summary

 Backend (New Files)

 ┌──────────────────────────────────────────────────────┬────────────┐
 │                         File                         │  Purpose   │
 ├──────────────────────────────────────────────────────┼────────────┤
 │                                                      │ ADMET      │
 │ backend/app/services/admet_service.py                │ prediction │
 │                                                      │  service   │
 ├──────────────────────────────────────────────────────┼────────────┤
 │                                                      │ Intelligen │
 │ backend/app/services/router_service.py               │ t model    │
 │                                                      │ routing    │
 ├──────────────────────────────────────────────────────┼────────────┤
 │                                                      │ BitNet     │
 │ backend/app/services/local_queue.py                  │ request    │
 │                                                      │ queue      │
 ├──────────────────────────────────────────────────────┼────────────┤
 │ backend/app/services/postprocessing/prompt_processor │ Complexity │
 │ .py                                                  │  scoring   │
 ├──────────────────────────────────────────────────────┼────────────┤
 │ backend/app/services/postprocessing/admet_processor. │ ADMET      │
 │ py                                                   │ formatting │
 ├──────────────────────────────────────────────────────┼────────────┤
 │ backend/app/services/postprocessing/export_processor │ Export     │
 │ .py                                                  │ utilities  │
 ├──────────────────────────────────────────────────────┼────────────┤
 │ backend/app/api/v1/endpoints/admet.py                │ ADMET API  │
 │                                                      │ endpoints  │
 ├──────────────────────────────────────────────────────┼────────────┤
 │ backend/tests/regression/test_admet_service.py       │ ADMET      │
 │                                                      │ tests      │
 ├──────────────────────────────────────────────────────┼────────────┤
 │ backend/tests/regression/test_router_service.py      │ Router     │
 │                                                      │ tests      │
 ├──────────────────────────────────────────────────────┼────────────┤
 │ backend/tests/regression/test_local_queue.py         │ Queue      │
 │                                                      │ tests      │
 └──────────────────────────────────────────────────────┴────────────┘

 Backend (Modified Files)

 ┌───────────────────────────────────────┬───────────────────────────┐
 │                 File                  │          Change           │
 ├───────────────────────────────────────┼───────────────────────────┤
 │ backend/app/core/container.py         │ Register new services and │
 │                                       │  processors               │
 ├───────────────────────────────────────┼───────────────────────────┤
 │ backend/app/services/multi_provider.p │ Add Provider.LOCAL,       │
 │ y                                     │ update MODE_PRIORITIES    │
 ├───────────────────────────────────────┼───────────────────────────┤
 │ backend/app/core/config.py            │ Add LOCAL_MODEL_ENABLED,  │
 │                                       │ LOCAL_MODEL_URL           │
 ├───────────────────────────────────────┼───────────────────────────┤
 │ backend/requirements.txt              │ Add PyTDC, medchem,       │
 │                                       │ datamol, deepchem         │
 ├───────────────────────────────────────┼───────────────────────────┤
 │ backend/app/services/pubmed_service.p │ Add summarize_results()   │
 │ y                                     │ method                    │
 ├───────────────────────────────────────┼───────────────────────────┤
 │ backend/app/services/ddi_service.py   │ Add generate_clinical_adv │
 │                                       │ ice() method              │
 └───────────────────────────────────────┴───────────────────────────┘

 Frontend (New Files)

 ┌───────────────────────────────────────────────────────┬───────────┐
 │                         File                          │  Purpose  │
 ├───────────────────────────────────────────────────────┼───────────┤
 │ frontend/src/app/lab/page.tsx                         │ Lab Hub   │
 │                                                       │ route     │
 ├───────────────────────────────────────────────────────┼───────────┤
 │ frontend/src/app/genetics/page.tsx                    │ Genetics  │
 │                                                       │ Hub route │
 ├───────────────────────────────────────────────────────┼───────────┤
 │                                                       │ Creation  │
 │ frontend/src/app/studio/page.tsx                      │ Studio    │
 │                                                       │ route     │
 ├───────────────────────────────────────────────────────┼───────────┤
 │                                                       │ ADMET     │
 │ frontend/src/components/lab/LabDashboard.tsx          │ Viewer,   │
 │                                                       │ DDI       │
 │                                                       │ Mapper    │
 ├───────────────────────────────────────────────────────┼───────────┤
 │ frontend/src/components/genetics/GeneticsDashboard.ts │ PharmGx,  │
 │ x                                                     │ GWAS visu │
 │                                                       │ alizers   │
 ├───────────────────────────────────────────────────────┼───────────┤
 │                                                       │ Outline   │
 │ frontend/src/components/studio/CreationStudio.tsx     │ editor,   │
 │                                                       │ preview   │
 ├───────────────────────────────────────────────────────┼───────────┤
 │                                                       │ Reusable  │
 │ frontend/src/components/chat/HandoffButton.tsx        │ handoff   │
 │                                                       │ component │
 ├───────────────────────────────────────────────────────┼───────────┤
 │ frontend/src/components/lab/__tests__/LabDashboard.te │ Lab tests │
 │ st.tsx                                                │           │
 └───────────────────────────────────────────────────────┴───────────┘

 Frontend (Modified Files)

 ┌─────────────────────────────────────────────────┬──────────────────┐
 │                      File                       │      Change      │
 ├─────────────────────────────────────────────────┼──────────────────┤
 │ frontend/src/components/chat/MessageContent.tsx │ Add handoff      │
 │                                                 │ buttons          │
 ├─────────────────────────────────────────────────┼──────────────────┤
 │ frontend/src/components/chat/ChatInput.tsx      │ Add queue        │
 │                                                 │ position toast   │
 └─────────────────────────────────────────────────┴──────────────────┘

 Infrastructure (New Files)

 ┌──────────────────────────┬─────────────────────────────────────────┐
 │           File           │                 Purpose                 │
 ├──────────────────────────┼─────────────────────────────────────────┤
 │ scripts/deploy_bitnet.sh │ VPS setup script                        │
 ├──────────────────────────┼─────────────────────────────────────────┤
 │ backend/.env.example     │ Add LOCAL_MODEL_ENABLED,                │
 │                          │ LOCAL_MODEL_URL                         │
 └──────────────────────────┴─────────────────────────────────────────┘

---

 Execution Order

 Sprint 1: Foundation (Week 1)

1. Add postprocessing processors (prompt, admet, export)
2. Update container.py with new registrations
3. Write regression tests FIRST

 Sprint 2: ADMET Backend (Week 2)

1. Implement ADMETService with ToxMCP patterns
2. Add ADMET API endpoints
3. Update requirements.txt
4. Run regression tests

 Sprint 3: Local Inference (Week 2-3)

1. Add Provider.LOCAL to multi_provider.py
2. Implement RouterService
3. Implement LocalInferenceQueue
4. Deploy BitNet to VPS (parallel work)

 Sprint 4: UI Strategy (Week 3-4)

1. Create Hub routes (/lab, /genetics, /studio)
2. Implement LabDashboard component
3. Implement GeneticsDashboard component
4. Implement CreationStudio component
5. Add HandoffButton to chat

 Sprint 5: Integration (Week 4-5)

1. End-to-end testing
2. VPS deployment
3. Smoke tests
4. Documentation update
