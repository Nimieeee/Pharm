# Year 1 Implementation Plan — Complete Technical Spec

> **Version**: 2.0 · March 2026
> **Scope**: 8 workstreams with full backend, frontend, UI/UX, and anti-regression details
> **Total Effort**: ~90-120 hours over 4 months

---

## Table of Contents

1. [Existing Assets](#existing-assets)
2. [WS1: Mermaid Frequency Fix](#ws1-mermaid-frequency-fix)
3. [WS2: Mermaid AI Self-Repair](#ws2-mermaid-ai-self-repair)
4. [WS3: Manuscript Export Upgrade](#ws3-manuscript-export-upgrade)
5. [WS4: Citation Manager](#ws4-citation-manager)
6. [WS5: PubMed Direct Search](#ws5-pubmed-direct-search)
7. [WS6: Drug-Drug Interaction Engine](#ws6-drug-drug-interaction-engine)
8. [WS7: GWAS Variant Lookup](#ws7-gwas-variant-lookup)
9. [WS8: PharmGx Reporter](#ws8-pharmgx-reporter)
10. [Anti-Regression Strategy](#anti-regression-strategy)
11. [Timeline](#timeline)

---

## Existing Assets

| Asset | File | What It Does |
|-------|------|-------------|
| DOCX/PDF Export | `backend/app/api/v1/endpoints/export.py` (303 lines) | Kroki mermaid→PNG + Benchside watermark |
| Mermaid Validator | `backend/app/services/mermaid_validator.py` (313 lines) | Regex auto-correction |
| Mermaid Processor | `backend/app/services/postprocessing/mermaid_processor.py` (425 lines) | Production singleton |
| Mermaid Tests | `backend/tests/regression/test_mermaid.py` (341 lines, 21 tests) | Performance + correctness |
| Multi-Provider | `backend/app/services/multi_provider.py` (464 lines) | 4 providers, 5 modes |
| System Prompt | `backend/app/services/ai.py:507-550` | Mermaid instructions |
| MermaidRenderer | `frontend/src/components/chat/MermaidRenderer.tsx` (524 lines) | Client-side render + refresh |
| ChatMessage | `frontend/src/components/chat/ChatMessage.tsx` (456 lines) | Already has `citations` interface |
| DeepResearchUI | `frontend/src/components/chat/DeepResearchUI.tsx` (418 lines) | SSE progress pattern |
| Image Gen | `backend/app/services/image_gen.py` (109 lines) | Pollinations API |
| Test Suite | `backend/tests/` (25 files, 5 dirs) | regression/, integration/, unit/ |

---

## WS1: Mermaid Frequency Fix

**Effort**: 30 min · **Priority**: P0

### Backend

#### [MODIFY] `backend/app/services/ai.py` — Line 517

```diff
-- You CAN and SHOULD generate **Mermaid diagrams** for any visualization request:
+- You CAN generate **Mermaid diagrams** ONLY when the user explicitly asks for one:
+  - Trigger words: "draw", "diagram", "flowchart", "visualize", "map out"
+  - Do NOT proactively add diagrams to text-based answers
```

### UI/UX Impact

- **Before**: ~8/10 responses include unwanted diagrams, cluttering the chat
- **After**: Diagrams appear only when requested, chat feels cleaner
- **No frontend changes needed** — this is purely a system prompt edit

### Verification

```bash
pytest tests/regression/test_mermaid.py -v  # Existing tests unchanged
# Manual: Send 10 pharmacology questions → target ≤2/10 with diagrams
```

---

## WS2: Mermaid AI Self-Repair

**Effort**: 4-6 hrs · **Priority**: P0

### Backend

#### [MODIFY] `backend/app/api/v1/endpoints/chat.py` — Add endpoint

```python
@router.post("/mermaid/repair")
async def repair_mermaid(request: MermaidRepairRequest,
                         current_user: User = Depends(get_current_user)):
    repaired = await ai_service.repair_mermaid_syntax(
        code=request.code, error=request.error)
    return {"repaired_code": repaired}
```

#### [MODIFY] `backend/app/services/ai.py` — Add method

```python
async def repair_mermaid_syntax(self, code: str, error: str) -> str:
    prompt = f"""Fix this Mermaid diagram syntax error.
Error: {error}
Broken code:
```mermaid
{code}
```
Return ONLY the corrected mermaid code. No explanation."""
    response = await self.multi_provider.chat_completion(
        mode="fast", messages=[{"role": "user", "content": prompt}],
        max_tokens=2000, temperature=0.0)
    return response.strip()
```

### Frontend

#### [MODIFY] `frontend/src/components/chat/MermaidRenderer.tsx`

**What changes in the UI**:
- Refresh button gets a **two-stage behavior**:
  1. First click: existing regex fix (instant, ~50ms)
  2. If still broken after 500ms: auto-calls `/mermaid/repair` endpoint
- During AI repair: button shows spinner icon (`Loader2` from lucide-react)
- On success: diagram re-renders with smooth fade-in (`framer-motion`)
- On failure: toast notification "Couldn't repair diagram" via `sonner`

```tsx
const handleManualRefresh = async () => {
  setRefreshKey(prev => prev + 1);
  renderDiagram(true);  // Attempt 1: regex
  
  setTimeout(async () => {
    if (renderError) {
      setIsRepairing(true);  // Show spinner on button
      try {
        const resp = await fetch('/api/v1/chat/mermaid/repair', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json',
                     'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ code: rawCode, error: renderError })
        });
        const { repaired_code } = await resp.json();
        if (repaired_code) {
          setCode(repaired_code);
          renderDiagram(true);
          toast.success("Diagram repaired!");
        }
      } catch (e) {
        toast.error("Couldn't repair diagram");
      } finally {
        setIsRepairing(false);
      }
    }
  }, 500);
};
```

**UI states for refresh button**:

| State | Icon | Label | Color |
|-------|------|-------|-------|
| Idle (no error) | `RefreshCw` | "Refresh" | `text-slate-400` |
| Error shown | `RefreshCw` | "Repair" | `text-amber-500` (pulsing) |
| AI repairing | `Loader2 animate-spin` | "Repairing..." | `text-amber-500` |
| Repair success | `Check` (2s) | "Fixed!" | `text-green-500` |

### Verification

```bash
pytest tests/regression/test_mermaid.py -v
pytest tests/test_mermaid_validator.py -v
# NEW: tests/test_mermaid_repair.py
# Test: POST broken "graph TD\nA-->B" → returns valid mermaid
```

---

## WS3: Manuscript Export Upgrade

**Effort**: 8-12 hrs · **Priority**: P1

### Backend

#### [MODIFY] `backend/app/api/v1/endpoints/export.py` — Add endpoint

```python
@router.get("/conversations/{conversation_id}/export/manuscript")
async def export_manuscript_docx(
    conversation_id: UUID,
    style: str = Query("report", enum=["report", "manuscript", "plain"]),
    current_user: User = Depends(get_export_user)):
    """Export as structured manuscript with sections"""
    # 1. Fetch AI messages
    # 2. AI restructures into sections (via fast mode)
    # 3. Build DOCX with python-docx: title page, TOC, headers, page numbers
```

#### [NEW] `backend/app/services/manuscript_formatter.py` (~250 lines)

```python
class ManuscriptFormatter:
    STYLES = {
        "report": ["Executive Summary", "Introduction", "Findings",
                    "Discussion", "Conclusion", "References"],
        "manuscript": ["Abstract", "Introduction", "Methods", "Results",
                       "Discussion", "References"],
    }
    
    async def structure_content(self, messages: list, style: str) -> dict:
        """AI restructures chat messages into manuscript sections"""
    
    def build_docx(self, structured: dict) -> bytes:
        """Build DOCX with:
        - Title page (Benchside branding)
        - Table of Contents (auto-generated)
        - Numbered heading hierarchy (H1, H2, H3)
        - Page numbers in footer
        - 'Generated by Benchside' watermark
        - APA/Vancouver citations from WS4 if available
        """
```

### Frontend

#### [MODIFY] `frontend/src/components/chat/ChatMessage.tsx`

**What changes in the UI**:
- Export dropdown (existing "Copy" button area) gets new options:
  - "Export as Chat" (existing behavior)
  - **"Export as Manuscript"** (new — triggers `/export/manuscript`)
  - **"Export as Report"** (new — same endpoint, `style=report`)
- Dropdown uses existing framer-motion `AnimatePresence` pattern
- Clicking triggers download of `.docx` file

```tsx
// Add to the actions row in ChatMessage (near Copy button, line ~100)
<Menu>
  <MenuButton className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">
    <FileText className="w-4 h-4 text-slate-400" />
  </MenuButton>
  <MenuItems>
    <MenuItem onClick={() => exportAs("plain")}>Export as Chat</MenuItem>
    <MenuItem onClick={() => exportAs("manuscript")}>Export as Manuscript</MenuItem>
    <MenuItem onClick={() => exportAs("report")}>Export as Report</MenuItem>
  </MenuItems>
</Menu>
```

**New UI element — Export Format Picker**:
- Small dropdown menu, appears from the `FileText` icon
- Glassmorphism style matching existing UI (`bg-surface/80 backdrop-blur-sm`)
- Shows download progress with a small spinner
- On complete: toast "Manuscript downloaded" with file size

### Verification

```bash
# tests/test_manuscript_export.py
# Test: POST conversation → get valid DOCX bytes (starts with PK ZIP magic)
# Test: DOCX contains TOC, page numbers, at least 3 heading levels
pytest tests/test_manuscript_export.py -v
```

---

## WS4: Citation Manager

**Effort**: 12-16 hrs · **Priority**: P1

### Backend

#### [NEW] `backend/app/services/citation_service.py` (~300 lines)

```python
class CitationService:
    async def resolve_doi(self, doi: str) -> dict:
        """GET https://api.crossref.org/works/{doi} → metadata"""
    
    async def resolve_pmid(self, pmid: str) -> dict:
        """GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
        ?db=pubmed&id={pmid}&rettype=xml → metadata"""
    
    def format_citation(self, metadata: dict, style: str = "apa") -> str:
        """APA: Author (Year). Title. Journal, Vol(Issue), Pages. doi:X
        Vancouver: Author. Title. Journal. Year;Vol(Issue):Pages.
        BibTeX: @article{key, author={...}, ...}"""
    
    async def extract_and_resolve(self, text: str) -> list[dict]:
        """Regex-detect DOIs (10.xxxx/xxxx) and PMIDs in AI output,
        resolve via CrossRef/PubMed, return formatted citations"""

    def generate_bibtex_file(self, citations: list[dict]) -> str:
        """Generate .bib file content from resolved citations"""
```

#### [MODIFY] `backend/app/services/postprocessing/__init__.py`

Add citation extraction to postprocessing pipeline:
```python
# After existing mermaid processing
citations = await citation_service.extract_and_resolve(text)
if citations:
    # Append formatted reference list to response
    text += "\n\n---\n### References\n"
    for i, c in enumerate(citations, 1):
        text += f"{i}. {c['formatted']}\n"
```

### Frontend

#### [NEW] `frontend/src/components/chat/CitationPanel.tsx` (~150 lines)

**What it looks like**:
- Small collapsible panel below AI messages that contain citations
- **Trigger**: Auto-detects when `message.citations` array is non-empty (interface already exists in `ChatMessage.tsx` line 17-29!)
- **Panel UI**: Amber-themed badge "3 References" → expands to show cards
- Each citation card shows: Author, Title, Journal, Year, DOI link
- **Action buttons per citation**: "Copy APA" · "Copy BibTeX" · "Open DOI"
- **Bulk actions**: "Download .bib" · "Copy All (APA)"

```tsx
interface CitationPanelProps {
  citations: Message["citations"];  // Already defined in ChatMessage.tsx!
  onExportBib: () => void;
}

// Renders as:
<motion.div className="border-t border-amber-200/30 mt-3 pt-3">
  <button onClick={toggle} className="flex items-center gap-2 text-xs text-amber-600">
    <BookOpen className="w-3.5 h-3.5" />
    {citations.length} References
    <ChevronDown className={`w-3 h-3 transition ${expanded ? 'rotate-180' : ''}`} />
  </button>
  <AnimatePresence>
    {expanded && (
      <motion.div initial={{height:0}} animate={{height:"auto"}} exit={{height:0}}>
        {citations.map(c => <CitationCard key={c.id} citation={c} />)}
        <button onClick={onExportBib}>Download .bib</button>
      </motion.div>
    )}
  </AnimatePresence>
</motion.div>
```

**Design**: Matches the source panel in `DeepResearchUI.tsx` (amber accents, small text, expand/collapse)

### Verification

```bash
# tests/test_citation_service.py
# Test: resolve_doi("10.1038/s41586-021-03819-2") → valid metadata
# Test: resolve_pmid("34265844") → valid metadata
# Test: format_citation(metadata, "apa") → valid APA string
# Test: extract_and_resolve("text with doi:10.1234/test") → 1 citation
pytest tests/test_citation_service.py -v
```

---

## WS5: PubMed Direct Search

**Effort**: 8-12 hrs · **Priority**: P1

### Backend

#### [NEW] `backend/app/services/pubmed_service.py` (~200 lines)

```python
class PubMedService:
    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    async def search(self, query: str, max_results: int = 20) -> list[dict]:
        """1. esearch → PMIDs  2. efetch → metadata
        Returns [{title, authors, journal, year, pmid, doi, abstract}]"""
    
    async def get_article(self, pmid: str) -> dict:
        """Full metadata for a single PMID"""
```

#### [NEW] Endpoint in `backend/app/api/v1/endpoints/chat.py`

```python
@router.get("/pubmed/search")
async def search_pubmed(query: str, max_results: int = 20):
    return await pubmed_service.search(query, max_results)
```

### Frontend

#### [NEW] `frontend/src/components/chat/PubMedResults.tsx` (~200 lines)

**What it looks like**:
- Rendered inline in AI responses when PubMed results are returned
- **Card grid** (2 columns on desktop, 1 on mobile) showing article cards
- Each card: Title (bold, linked to PubMed), Authors (truncated), Journal + Year, abstract preview (2 lines)
- "View Abstract" expands the card (same `AnimatePresence` pattern as `DeepResearchUI.tsx` source cards)
- "Cite" button per card → copies APA format to clipboard (uses WS4 CitationService)

**Design matches**: Same styling as Deep Research source cards — amber accents, glassmorphism, expand/collapse

#### [MODIFY] `frontend/src/components/chat/ChatInput.tsx`

Add PubMed search shortcut:
- When user types `/pubmed SGLT2 inhibitors`, intercept and call `/pubmed/search`
- Results render as `PubMedResults` component in the chat
- Small "PubMed" badge appears next to results

### Verification

```bash
# tests/test_pubmed_service.py
# Test: search("SGLT2 inhibitors", 5) → 5 results with titles
# Test: get_article("34265844") → dict with all required fields
pytest tests/test_pubmed_service.py -v
```

---

## WS6: Drug-Drug Interaction Engine

**Effort**: 16-20 hrs · **Priority**: P1

### Backend

#### [NEW] `backend/app/services/ddi_service.py` (~350 lines)

```python
class DDIService:
    async def resolve_drug(self, name: str) -> str:
        """GET https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug} → RxCUI"""
    
    async def check_interaction(self, drug_a: str, drug_b: str) -> dict:
        """GET https://rxnav.nlm.nih.gov/REST/interaction/list.json
        ?rxcuis={rxcui_a}+{rxcui_b}
        Returns: {severity, description, mechanism, evidence_level, alternatives}"""
    
    async def check_polypharmacy(self, drugs: list[str]) -> list[dict]:
        """Check all pairwise interactions"""
```

All APIs free, no key needed.

#### [NEW] Endpoint in `backend/app/api/v1/endpoints/chat.py`

```python
@router.post("/ddi/check")
async def check_ddi(request: DDIRequest):
    return await ddi_service.check_interaction(request.drug_a, request.drug_b)

@router.post("/ddi/polypharmacy")  
async def check_polypharmacy(request: PolypharmacyRequest):
    return await ddi_service.check_polypharmacy(request.drugs)
```

### Frontend

#### [NEW] `frontend/src/components/chat/DDIResult.tsx` (~250 lines)

**What it looks like**:
- Rendered inline when AI detects drug interaction query or user uses `/ddi warfarin aspirin`
- **Severity banner** at top:
  - 🔴 Major: red gradient banner, bold warning
  - 🟡 Moderate: amber banner
  - 🟢 Minor: green subtle banner
- **Interaction details card**:
  - Mechanism (e.g., "CYP2C9 inhibition increases warfarin levels")
  - Evidence level (★★★/★★☆/★☆☆)
  - Clinical significance
  - Recommended action
- **Alternatives section**: "Consider instead: {alternative drugs}"
- **Disclaimer footer**: "For educational purposes only. Consult your healthcare provider."

**Polypharmacy view** (3+ drugs):
- Matrix/grid view showing all pairwise interactions
- Color-coded cells (red/amber/green)
- Each cell expandable to show details

```tsx
// Severity banner component
<div className={`rounded-lg p-4 ${
  severity === "Major" ? "bg-red-50 dark:bg-red-950/30 border-red-200" :
  severity === "Moderate" ? "bg-amber-50 dark:bg-amber-950/30 border-amber-200" :
  "bg-green-50 dark:bg-green-950/30 border-green-200"
}`}>
  <div className="flex items-center gap-2">
    <AlertTriangle className="w-5 h-5" />
    <span className="font-semibold">{severity} Interaction</span>
  </div>
  <p className="text-sm mt-2">{description}</p>
</div>
```

### Verification

```bash
# tests/test_ddi_service.py
# Test: check_interaction("warfarin", "aspirin") → severity "Major"
# Test: check_interaction("metformin", "lisinopril") → Minor or None
# Test: check_polypharmacy(["warfarin","aspirin","omeprazole"]) → 3 pairs
# Test: resolve_drug("tylenol") → returns valid RxCUI
pytest tests/test_ddi_service.py -v
```

---

## WS7: GWAS Variant Lookup

**Effort**: 12-16 hrs · **Priority**: P2

### Backend

#### [NEW] `backend/app/services/gwas_service.py` (~300 lines)

Adapted from `research/clawbio/skills/gwas-lookup/`. Queries 9 databases in parallel.

```python
class GWASService:
    async def lookup_variant(self, rsid: str) -> dict:
        """Parallel queries to: Ensembl, GWAS Catalog, Open Targets,
        UK Biobank PheWeb, FinnGen, GTEx, JENGER BBJ, ClinVar, CADD
        Returns: {variant_info, associations[], eqtls[], phewas[], credible_sets[]}"""
```

#### [NEW] Endpoint in `backend/app/api/v1/endpoints/chat.py`

```python
@router.get("/gwas/lookup/{rsid}")
async def gwas_lookup(rsid: str):
    return await gwas_service.lookup_variant(rsid)
```

### Frontend

#### [NEW] `frontend/src/components/chat/GWASResult.tsx` (~300 lines)

**What it looks like**:
- **Variant header**: rsID, chromosome position, alleles, gene context
- **Association table**: Sortable by p-value, trait, population
  - Rows colored by significance (genome-wide significant = amber highlight)
- **Database chips**: Shows which of 9 databases returned results (filled vs outline badges)
- **eQTL panel**: Gene expression effects from GTEx (collapsible)
- **PheWAS plot**: If matplotlib-generated plot available, embedded as image

**Design**: Follows `DeepResearchUI.tsx` two-panel pattern — results left, database status right

### Verification

```bash
# tests/test_gwas_service.py
# Test: lookup_variant("rs7903146") → returns ensembl data + GWAS hits
# Test: lookup_variant("rs_invalid") → graceful error response
pytest tests/test_gwas_service.py -v
```

---

## WS8: PharmGx Reporter

**Effort**: 16-20 hrs · **Priority**: P2

### Backend

#### [NEW] `backend/app/services/pharmgx_service.py` (~400 lines)

Adapted from `research/clawbio/skills/pharmgx-reporter/`. Zero external dependencies.

```python
class PharmGxService:
    # 12 genes, 31 SNPs, 51 drugs — all data embedded as constants
    
    async def generate_report(self, file_content: bytes, filename: str) -> dict:
        """Parse 23andMe/AncestryDNA → 12-gene PGx report with CPIC guidance
        Returns: {patient_id, genes: [{gene, genotype, phenotype, drugs: [{name, guidance}]}]}"""
    
    async def single_drug_lookup(self, file_content: bytes, drug_name: str) -> dict:
        """Quick lookup for one drug"""
```

#### [MODIFY] `backend/app/api/v1/endpoints/chat.py`

Route `.txt` file uploads with genetic data patterns to PharmGxService:
```python
@router.post("/pharmgx/report")
async def generate_pharmgx_report(file: UploadFile):
    content = await file.read()
    return await pharmgx_service.generate_report(content, file.filename)
```

### Frontend

#### [NEW] `frontend/src/components/chat/PharmGxReport.tsx` (~350 lines)

**What it looks like**:
- **Full-width card** replacing normal chat response (same pattern as `DeepResearchUI.tsx`)
- **Header**: "Pharmacogenomic Report" with gene count badge
- **Gene cards** (accordion): Each gene shows:
  - Gene name + genotype (e.g., `CYP2D6 *1/*2`)
  - Metabolizer phenotype badge: `Normal` (green), `Intermediate` (amber), `Poor` (red), `Ultra-rapid` (blue)
  - Drug list under each gene with CPIC guidance
- **Drug search**: Search box to find specific drug across all genes
- **Disclaimer banner** at bottom: Red border, "For educational/research purposes only"

**Upload trigger**:
- When user uploads a `.txt` file, `ChatInput.tsx` checks if first line matches 23andMe/AncestryDNA format
- If yes: shows modal "Genetic data detected. Generate PharmGx report?" with Accept/Cancel
- Accept → POST to `/pharmgx/report` → render `PharmGxReport`

### Verification

```bash
# tests/test_pharmgx_service.py (use ClawBio demo patient)
# Test: generate_report(demo_patient.txt) → 12 gene profiles
# Test: single_drug_lookup(demo_content, "warfarin") → VKORC1 + CYP2C9 guidance
pytest tests/test_pharmgx_service.py -v
```

---

---

## Anti-Regression Strategy

### Test Architecture

```
backend/tests/
├── regression/
│   ├── test_mermaid.py              # [EXISTING] 21 tests
│   ├── test_mermaid_validator.py     # [EXISTING] 12 tests (moved here)
│   ├── test_export_regression.py     # [NEW] Ensure existing export still works
│   └── test_ws_regression.py         # [NEW] Cross-workstream regression
├── test_citation_service.py          # [NEW] WS4
├── test_pubmed_service.py            # [NEW] WS5
├── test_ddi_service.py               # [NEW] WS6
├── test_gwas_service.py              # [NEW] WS7
├── test_pharmgx_service.py           # [NEW] WS8
├── test_mermaid_repair.py            # [NEW] WS2
└── test_manuscript_export.py         # [NEW] WS3
```

### Cross-Workstream Regression Tests

#### [NEW] `backend/tests/regression/test_ws_regression.py`

```python
"""Ensures no workstream breaks another"""

class TestCrossWorkstreamRegression:
    def test_import_all_services(self):
        """All new services import without circular deps"""
        from app.services.citation_service import CitationService
        from app.services.pubmed_service import PubMedService
        from app.services.ddi_service import DDIService
        from app.services.gwas_service import GWASService
        from app.services.pharmgx_service import PharmGxService
        from app.services.manuscript_formatter import ManuscriptFormatter

    def test_postprocessing_unchanged(self):
        """Postprocessing pipeline still works after citation injection"""
        from app.services.postprocessing import postprocess_response
        result = postprocess_response("Simple text without citations")
        assert "Simple text" in result

    def test_mermaid_still_works_after_ws1(self):
        """Mermaid processing unchanged after frequency fix"""
        from app.services.mermaid_validator import MermaidValidator
        v = MermaidValidator()
        fixed = v.auto_correct("graph TD\nA-->B")
        assert "graph TD" in fixed

    def test_export_still_works_after_ws3(self):
        """Original export endpoint not broken by manuscript addition"""
        # Original /export/docx route still returns valid DOCX
```

### Pre-Deployment Checklist

| Check | Command/Action | Pass Criteria |
|-------|---------------|---------------|
| All regression tests | `pytest tests/regression/ -v` | 0 failures |
| All new service tests | `pytest tests/test_*_service.py -v` | 0 failures |

| Import smoke test | `python -c "from app.services.X import Y"` per service | No ImportError |
| Mermaid renders | Send diagram request in chat | Renders correctly |
| Export DOCX works | Export any conversation | Valid file downloads |
| Deep Research works | Run a research query | Report generates |
| Chat streaming works | Send any message | Response streams |
| Image gen works | Request structure image | Image renders |

### CI Pipeline

#### [NEW] `.github/workflows/regression.yml`

```yaml
name: Regression Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest tests/regression/ -v --tb=short
```

---

## Timeline

```
Month 1:
  Week 1:   WS1 (30 min) + WS2 (4-6 hrs)
  Week 2-3: WS3 Manuscript export (8-12 hrs)
  Week 3-4: WS4 Citation manager (12-16 hrs)

Month 2:
  Week 1-2: WS5 PubMed search (8-12 hrs)
  Week 2-4: WS6 DDI engine (16-20 hrs)

Month 3:
  Week 1-2: WS7 GWAS lookup (12-16 hrs)

Month 4:
  Week 1-3: WS8 PharmGx reporter (16-20 hrs)
  Week 4:   Anti-regression suite + CI pipeline
```

**Total**: ~90-120 hours over 4 months

---

## Frontend File Map (New Components)

```
frontend/src/components/chat/
├── CitationPanel.tsx        # [NEW] WS4 — citation cards + BibTeX export
├── PubMedResults.tsx        # [NEW] WS5 — article cards, inline in chat
├── DDIResult.tsx            # [NEW] WS6 — severity banner + interaction details
├── GWASResult.tsx           # [NEW] WS7 — variant associations + database chips
├── PharmGxReport.tsx        # [NEW] WS8 — gene cards with metabolizer badges
├── ChatMessage.tsx          # [MODIFY] — export dropdown, citation panel hook
├── ChatInput.tsx            # [MODIFY] — /pubmed, /ddi shortcuts, genetic file detection
├── MermaidRenderer.tsx      # [MODIFY] WS2 — AI repair on refresh button
└── DeepResearchUI.tsx       # [REFERENCE] — pattern to follow for all new components
```

---

> [!CAUTION]
> **Medical Disclaimer**: DDI (WS6) and PharmGx (WS8) produce health-related output. Both MUST include "For educational/research purposes only" disclaimers.

> [!NOTE]
> **No paid API keys needed**: All external APIs (CrossRef, PubMed E-utilities, RxNorm, NLM Drug Interaction, Ensembl, GWAS Catalog) are free and public.
