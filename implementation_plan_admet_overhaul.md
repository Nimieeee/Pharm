# ADMET Lab Overhaul + Auth/Theme Fixes

> [!CAUTION]
> This plan supersedes the previous [implementation_plan_auth_landing.md](file:///Users/mac/.gemini/antigravity/brain/6ee91e3d-18de-414d-8d7e-743d9139ae2d/implementation_plan_auth_landing.md). It includes those auth/theme fixes plus the full ADMET Lab overhaul.

---

## Diagnosis Summary

From the screenshot and code investigation:

| Issue | Root Cause | File(s) |
|:---|:---|:---|
| Empty "Key Properties" section | `/analyze` returns **markdown string**, frontend regex-parses it. When ADMET-AI engine is down → RDKit fallback → sparse markdown → parser finds nothing | `admet_service.py:395-435`, `LabDashboard.tsx:52-130` |
| Raw text leak ("ADMET Analysis Report", "Service Notice", "Detailed Results") | Frontend regex only matches `### Category` + `- **Name**: value`. `## ADMET Analysis Report`, `## Detailed Results` headers don't match and fall to `summary[]` | `LabDashboard.tsx:90-97` |
| "Failed to render structure" | SVG endpoint calls RDKit on VPS but the SMILES may be invalid or RDKit import fails locally | `MoleculePreview.tsx:37` |
| 401 errors on all hubs | `sb-access-token` key instead of `token` in localStorage | 6 files, 11 call sites |
| Light mode unreadable | Hardcoded `text-white`, `bg-black/40` | [CreationStudio.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/studio/CreationStudio.tsx), [GeneticsDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/genetics/GeneticsDashboard.tsx) |
| Upload button dead | No [onClick](file:///Users/mac/Desktop/phhh/frontend/src/app/page.tsx#47-50) handler | `LabDashboard.tsx:265-271` |
| Batch limited to 20 | Hard cap in `admet.py:52` and `admet_service.py:644` | Both files |
| No batch UI | Only single SMILES text input | [LabDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/LabDashboard.tsx) |
| CSV is single-molecule only | [export_as_csv()](file:///Users/mac/Desktop/phhh/backend/app/services/admet_service.py#527-545) takes a single dict | `admet_service.py:527-544` |

---

## Iron Rules of Implementation

> [!IMPORTANT]
> These rules are derived from **CLAUDE.md** and represent hard constraints based on past production bugs.

### Debugging & Anti-Regression Protocol
1. **NO FIXES WITHOUT ROOT CAUSE** — (Iron Law)trace back to components boundaries.
2. **Four Phases of Systematic Debugging** — Root Cause → Pattern Analysis → Failure Mode Analysis (FMA) → Implementation.
3. **Test-first** — Create a failing test case in `tests/regression/` FIRST.
4. **VPS Mandatory** — ALL backend tests/verification MUST run on the Lightsail VPS (`ubuntu@15.237.208.231`). Local Mac lacks RDKit/ADMET-AI.

### Error Prevention Rules (from CLAUDE.md Section 6)
| Rule | Requirement |
|:---|:---|
| **R1: HTML Decoding** | Unescape entities (`&quot;`, `&lt;`) before parsing structured syntax (Mermaid, JSON). |
| **R2: FastAPI DI** | NEVER call `get_db()`/`Depends()` directly. They are generator factories. |
| **R3: Stale Closures** | Use `useRef` for async state access in `useEffect`/`setTimeout` to avoid stale reads. |
| **R4: Idempotent Assembly** | Build output once. NEVER "append → strip → re-append". |
| **R5: UUID Validation** | Validate `conversationId` vs UUID regex before API calls. |
| **R6: Directional Scoring** | RISK endpoints (Tox) = low is 🟢. BENEFIT (HIA) = high is 🟢. No universal thresholds. |
| **R7: Pydantic Settings** | Use `settings.MISTRAL_API_KEY`, NOT `os.environ.get()` (Pydantic doesn't export to shell). |

### ADMET Architectural Constraints
- **Port 7861**: Primary engine runs as `admet-engine` on port 7861.
- **Valid SMILES Only**: [drugPool.ts](file:///Users/mac/Desktop/phhh/frontend/src/constants/drugPool.ts) must NOT contain peptide sequences (crushes RDKit).
- **No Fake Endpoints**: Do NOT add Nephrotoxicity/Neurotoxicity to ADMET-AI results (ADMETlab-only).

---

## Part 1: Structured JSON API (Fix Empty Properties)

### Problem

The current architecture is:
```
Backend: predict_admet() → dict{46 keys} → format_report() → markdown string
Frontend: regex-parse markdown → ADMETPropertyCard[]
```

This is fragile — when the markdown format doesn't match the regex, properties vanish.

### Solution

Add a new `/analyze/v2` endpoint that returns **structured JSON** alongside the markdown. The frontend will render from JSON directly — no parsing.

#### [NEW] Backend: Structured response model

```python
# In admet.py — new endpoint

class ADMETPropertyResponse(BaseModel):
    """Structured ADMET property"""
    name: str           # Human label, e.g. "Human Intestinal Absorption"
    key: str            # Internal key, e.g. "HIA_Hou"
    value: float | int | str
    unit: str = ""
    percentile: float | None = None     # DrugBank percentile
    status: str = "neutral"             # "success" | "warning" | "danger" | "neutral"
    interpretation: str = ""            # e.g. "✅ High intestinal absorption"

class ADMETCategoryResponse(BaseModel):
    """Grouped category"""
    name: str           # e.g. "Absorption"
    properties: list[ADMETPropertyResponse]

class ADMETAnalysisResponse(BaseModel):
    """Full structured response"""
    success: bool
    smiles: str
    molecule_name: str | None = None
    svg: str | None = None
    engine: str         # "admet-ai (Chemprop v2)" | "RDKit (fallback)"
    categories: list[ADMETCategoryResponse]
    ai_interpretation: str | None = None
    report_markdown: str  # Legacy markdown for copy/share
```

#### [MODIFY] [admet.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/admet.py)

Replace the current `/analyze` endpoint to return structured JSON:

```python
@router.post("/analyze")
async def analyze_molecule(
    request: ADMETAnalysisRequest,
    current_user: User = Depends(get_current_user),
    admet_service = Depends(get_admet_service)
):
    try:
        # 1. Get raw predictions (dict with 46 keys)
        admet_data = await admet_service.predict_admet(request.smiles)
        
        # 2. Get SVG
        svg = None
        if request.include_svg:
            try:
                svg = await admet_service.get_svg(request.smiles)
            except Exception:
                pass
        
        # 3. Get AI interpretation
        ai_interpretation = None
        try:
            ai_interpretation = await admet_service._generate_ai_interpretation(admet_data)
        except Exception:
            pass
        
        # 4. Build structured categories from raw data
        categories = admet_service.processor.build_structured_categories(admet_data)
        
        # 5. Also generate markdown for copy/share
        report_md = admet_service.processor.format_report(admet_data, svg, ai_interpretation)
        
        return {
            "success": True,
            "smiles": request.smiles,
            "svg": svg,
            "engine": admet_data.get("_engine", "Unknown"),
            "categories": categories,
            "ai_interpretation": ai_interpretation,
            "report_markdown": report_md,
        }
    except Exception as e:
        raise HTTPException(500, detail=f"ADMET analysis failed: {str(e)}")
```

#### [MODIFY] [admet_processor.py](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/admet_processor.py)

Add `build_structured_categories()` method:

```python
def build_structured_categories(self, admet_data: Dict[str, Any]) -> list:
    """
    Build structured JSON categories from raw ADMET prediction dict.
    Returns list of {name, properties: [{name, key, value, unit, percentile, status, interpretation}]}
    """
    property_groups = {
        "Physicochemical": ["molecular_weight", "logP", "hydrogen_bond_donors", 
                           "hydrogen_bond_acceptors", "tpsa", "num_rotatable_bonds", 
                           "num_rings", "num_heavy_atoms", "stereo_centers"],
        "Drug Likeness": ["Lipinski", "QED", "PAINS_alert", "BRENK_alert", "NIH_alert"],
        "Absorption": ["HIA_Hou", "Caco2_Wang", "PAMPA_NCATS", "Pgp_Broccatelli",
                       "Solubility_AqSolDB", "Lipophilicity_AstraZeneca",
                       "HydrationFreeEnergy_FreeSolv", "Bioavailability_Ma"],
        "Distribution": ["BBB_Martins", "PPBR_AZ", "VDss_Lombardo"],
        "Metabolism": ["CYP1A2_Veith", "CYP2C9_Veith", "CYP2C19_Veith", 
                      "CYP2D6_Veith", "CYP3A4_Veith",
                      "CYP2C9_Substrate_CarbonMangels",
                      "CYP2D6_Substrate_CarbonMangels",
                      "CYP3A4_Substrate_CarbonMangels"],
        "Excretion": ["Clearance_Hepatocyte_AZ", "Clearance_Microsome_AZ",
                     "Half_Life_Obach"],
        "Toxicity": ["hERG", "AMES", "DILI", "ClinTox", "Carcinogens_Lagunin",
                    "LD50_Zhu", "Skin_Reaction",
                    "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase",
                    "NR-ER", "NR-ER-LBD", "NR-PPAR-gamma",
                    "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"],
    }
    
    categories = []
    for group_name, keys in property_groups.items():
        props = []
        for key in keys:
            if key in admet_data and admet_data[key] is not None:
                val = admet_data[key]
                label = self.header_labels.get(key, key.replace('_', ' ').title())
                interp = self.get_interpretation(key, val)
                
                # Determine status from interpretation emoji
                status = "neutral"
                if "✅" in interp: status = "success"
                elif "⚠️" in interp: status = "warning"
                elif "❌" in interp: status = "danger"
                
                # Get percentile if available
                percentile_key = f"{key}_drugbank_approved_percentile"
                percentile = admet_data.get(percentile_key)
                
                props.append({
                    "name": label,
                    "key": key,
                    "value": round(val, 4) if isinstance(val, float) else val,
                    "percentile": round(percentile, 2) if percentile else None,
                    "status": status,
                    "interpretation": interp.replace("✅ ", "").replace("⚠️ ", "").replace("❌ ", ""),
                })
        
        if props:
            categories.append({"name": group_name, "properties": props})
    
    return categories
```

#### [MODIFY] [LabDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/LabDashboard.tsx)

Replace the markdown-parsing `parsedData` useMemo with direct JSON consumption:

```tsx
// NEW interface — matches backend structured response
interface StructuredCategory {
  name: string;
  properties: {
    name: string;
    key: string;
    value: number | string;
    percentile?: number;
    status: 'success' | 'warning' | 'danger' | 'neutral';
    interpretation: string;
  }[];
}

interface ADMETResult {
  success: boolean;
  smiles: string;
  svg: string | null;
  engine: string;
  categories: StructuredCategory[];
  ai_interpretation: string | null;
  report_markdown: string;
}

// DELETE the parsedData useMemo entirely (lines 53-130)
// Render directly from result.categories:
{result.categories.map(cat => (
  <ADMETPropertyCard 
    key={cat.name}
    category={cat.name}
    properties={cat.properties.map(p => ({
      name: p.name,
      value: typeof p.value === 'number' ? p.value.toFixed(4) : p.value,
      status: p.status as StatusType,
      unit: p.percentile ? ` (${p.percentile}%ile)` : '',
    }))}
    icon={FlaskConical}
  />
))}
```

---

## Part 2: Batch SMILES Input

### Problem
Only a single `<input>` exists. No way to enter multiple SMILES.

### Solution
Add a **textarea mode toggle** — switch between single input and multi-line textarea.

#### [MODIFY] [LabDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/LabDashboard.tsx)

```tsx
const [inputMode, setInputMode] = useState<'single' | 'batch'>('single');
const [batchSmiles, setBatchSmiles] = useState('');

// In JSX — mode toggle above input:
<div className="flex items-center gap-2 mb-3">
  <button
    onClick={() => setInputMode('single')}
    className={`text-xs px-3 py-1 rounded-lg ${inputMode === 'single' ? 'bg-amber-500 text-white' : 'bg-[var(--surface-highlight)] text-[var(--text-muted)]'}`}
  >
    Single
  </button>
  <button
    onClick={() => setInputMode('batch')}
    className={`text-xs px-3 py-1 rounded-lg ${inputMode === 'batch' ? 'bg-amber-500 text-white' : 'bg-[var(--surface-highlight)] text-[var(--text-muted)]'}`}
  >
    Batch
  </button>
</div>

{inputMode === 'batch' ? (
  <textarea
    value={batchSmiles}
    onChange={(e) => setBatchSmiles(e.target.value)}
    placeholder="Enter one SMILES per line..."
    rows={6}
    className="w-full px-4 py-3 rounded-xl bg-[var(--surface-highlight)] border border-[var(--border)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:ring-2 focus:ring-amber-500/50 font-mono text-sm resize-y"
  />
) : (
  /* existing single input */
)}
```

---

## Part 3: SDF File Upload

### Problem
The "Upload" button has no [onClick](file:///Users/mac/Desktop/phhh/frontend/src/app/page.tsx#47-50) handler.

### Solution
Wire the Upload button to a hidden file input that accepts `.sdf` files and POSTs to `/api/v1/admet/batch`.

#### [MODIFY] [LabDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/LabDashboard.tsx)

```tsx
const fileInputRef = useRef<HTMLInputElement>(null);

const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0];
  if (!file) return;
  
  setIsLoading(true);
  setError('');
  
  try {
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/v1/admet/batch`, {
      method: 'POST',
      headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) },
      body: formData,
    });
    
    if (!response.ok) throw new Error('Upload failed');
    
    const data = await response.json();
    setBatchResults(data.results);
    toast.success(`Analyzed ${data.count} molecules`);
  } catch (err: any) {
    setError(err.message);
  } finally {
    setIsLoading(false);
  }
};

// Hidden input + wire upload button
<input ref={fileInputRef} type="file" accept=".sdf" className="hidden" onChange={handleFileUpload} />
<button onClick={() => fileInputRef.current?.click()} ...>
  <Upload ... /> Upload SDF
</button>
```

---

## Part 4: Per-Compound Results Display

### Problem
No batch results view exists.

### Solution
Show results as an **accordion list** — each molecule is a collapsible row. Clicking expands to show its ADMET categories.

#### [NEW] [BatchResultsView.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/BatchResultsView.tsx)

```tsx
interface BatchResult {
  index: number;
  smiles: string;
  molecule_name?: string;
  success: boolean;
  categories?: StructuredCategory[];
  error?: string;
}

// Accordion pattern:
// Header: [#] [SMILES truncated] [Status badge] [Expand ▼]
// Body: Grid of ADMETPropertyCards (same as single view)

export default function BatchResultsView({ results }: { results: BatchResult[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);
  
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <h3>Batch Results ({results.length} compounds)</h3>
        <button onClick={handleExportBatchCSV}>Export All CSV</button>
      </div>
      
      {results.map((r, i) => (
        <div key={i} className="rounded-xl border">
          {/* Header row — always visible */}
          <button onClick={() => setExpanded(expanded === i ? null : i)}>
            <span>#{r.index}</span>
            <span className="font-mono">{r.smiles.slice(0, 30)}...</span>
            <StatusBadge status={r.success ? 'success' : 'danger'} />
          </button>
          
          {/* Expanded detail — shows property cards */}
          {expanded === i && r.categories && (
            <div className="grid grid-cols-2 gap-4 p-4">
              {r.categories.map(cat => (
                <ADMETPropertyCard key={cat.name} category={cat.name} properties={cat.properties} />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

---

## Part 5: Batch/SDF Handling (Backend)

### Problem

1. Batch cap of 20 is too low for 1000-compound SDF files
2. [analyze_batch()](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/admet.py#27-68) calls [generate_report()](file:///Users/mac/Desktop/phhh/backend/app/services/admet_service.py#395-436) per molecule (slow — includes AI interpretation per molecule)
3. No batch CSV export

### Solution

#### [MODIFY] [admet.py](file:///Users/mac/Desktop/phhh/backend/app/api/v1/endpoints/admet.py) — `/batch` endpoint

```python
@router.post("/batch")
async def analyze_batch(
    file: UploadFile = File(None),
    smiles_list: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    admet_service = Depends(get_admet_service)
):
    import json
    molecules = []
    
    if file:
        content = await file.read()
        molecules = await admet_service.extract_smiles_from_sdf(content)
    elif smiles_list:
        raw = json.loads(smiles_list)
        # Accept both ["SMILES1", "SMILES2"] and [{"smiles": "...", "name": "..."}]
        molecules = [
            {"smiles": s, "name": f"Molecule {i+1}"} if isinstance(s, str) else s
            for i, s in enumerate(raw)
        ]
    
    if not molecules:
        raise HTTPException(400, "No SMILES provided")
    
    # Cap at 100 for now (up from 20), warn user
    total = len(molecules)
    capped = molecules[:100]
    
    results = await admet_service.analyze_batch_structured(capped)
    
    return {
        "success": True,
        "count": len(results),
        "total_submitted": total,
        "capped_at": 100 if total > 100 else None,
        "results": results
    }
```

#### [MODIFY] [admet_service.py](file:///Users/mac/Desktop/phhh/backend/app/services/admet_service.py)

Add `analyze_batch_structured()` — returns JSON, not markdown:

```python
async def analyze_batch_structured(self, molecules: list) -> list:
    """Batch analysis returning structured JSON per molecule."""
    results = []
    
    for i, mol in enumerate(molecules):
        smiles = mol["smiles"] if isinstance(mol, dict) else mol
        name = mol.get("name") if isinstance(mol, dict) else None
        
        try:
            admet_data = await self.predict_admet(smiles)
            categories = self.processor.build_structured_categories(admet_data)
            
            results.append({
                "index": i + 1,
                "smiles": smiles,
                "molecule_name": name,
                "success": True,
                "engine": admet_data.get("_engine", "Unknown"),
                "categories": categories,
            })
            await asyncio.sleep(0.1)
            
        except Exception as e:
            results.append({
                "index": i + 1,
                "smiles": smiles,
                "molecule_name": name,
                "success": False,
                "error": str(e),
            })
    
    return results
```

#### [NEW] Batch CSV endpoint

```python
# In admet.py
@router.post("/export/batch")
async def export_batch_csv(
    request: BatchExportRequest,  # { results: [...structured results...] }
    current_user: User = Depends(get_current_user),
    admet_service = Depends(get_admet_service)
):
    """Export batch results as one CSV with one row per molecule."""
    csv_content = admet_service.processor.format_batch_csv(request.results)
    
    return StreamingResponse(
        io.BytesIO(csv_content.encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=admet_batch.csv"}
    )
```

#### [MODIFY] [admet_processor.py](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/admet_processor.py)

```python
def format_batch_csv(self, results: list) -> str:
    """
    Format batch results as CSV.
    One row per molecule, columns = all unique property keys.
    """
    if not results:
        return "No results"
    
    # Collect all unique property keys across all molecules
    all_keys = []
    for r in results:
        if r.get("success") and r.get("categories"):
            for cat in r["categories"]:
                for prop in cat["properties"]:
                    if prop["key"] not in all_keys:
                        all_keys.append(prop["key"])
    
    # Header
    headers = ["#", "SMILES", "Name", "Engine"] + [
        self.header_labels.get(k, k) for k in all_keys
    ]
    lines = [",".join(headers)]
    
    # Rows
    for r in results:
        if not r.get("success"):
            row = [str(r["index"]), r["smiles"], r.get("molecule_name", ""), "FAILED"]
            row += [""] * len(all_keys)
            lines.append(",".join(row))
            continue
        
        # Build lookup from categories
        prop_lookup = {}
        for cat in r.get("categories", []):
            for prop in cat["properties"]:
                prop_lookup[prop["key"]] = prop["value"]
        
        row = [str(r["index"]), r["smiles"], r.get("molecule_name", ""), r.get("engine", "")]
        for key in all_keys:
            val = prop_lookup.get(key, "")
            row.append(str(val) if val != "" else "")
        
        lines.append(",".join(row))
    
    return "\n".join(lines)
```

---

## Part 6: Auth Token Fix (from previous plan)

Global find-and-replace across 6 files:

```diff
- localStorage.getItem('sb-access-token')
+ localStorage.getItem('token')
```

**Files**: [usePubMed.ts](file:///Users/mac/Desktop/phhh/frontend/src/hooks/usePubMed.ts), [useDDI.ts](file:///Users/mac/Desktop/phhh/frontend/src/hooks/useDDI.ts), [CreationStudio.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/studio/CreationStudio.tsx), [GeneticsDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/genetics/GeneticsDashboard.tsx), [LabDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/LabDashboard.tsx), [ChatMessage.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/chat/ChatMessage.tsx), [MermaidRenderer.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/chat/MermaidRenderer.tsx)

---

## Part 7: Light Mode Theme Fix (from previous plan)

Migrate [CreationStudio.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/studio/CreationStudio.tsx) and [GeneticsDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/genetics/GeneticsDashboard.tsx) from hardcoded `text-white`/`bg-black/40`/`bg-white/5` to CSS variables (`var(--text-primary)`, `var(--surface)`, etc.).

Reference: [LiteratureDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/literature/LiteratureDashboard.tsx) and [DDIDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/ddi/DDIDashboard.tsx) already use CSS variables correctly.

---

## Verification Plan

### Automated Tests (run on VPS)

**Existing test suite** — 612 lines, 20+ tests including directional scoring:
```bash
ssh -i ~/.ssh/lightsail_key ubuntu@15.237.208.231 \
  "cd /var/www/benchside-backend/backend && source .venv/bin/activate && pytest tests/regression/test_admet_service.py -v"
```

**New tests to add** in [test_admet_service.py](file:///Users/mac/Desktop/phhh/backend/tests/regression/test_admet_service.py):

```python
class TestBuildStructuredCategories:
    def test_returns_categories_from_flat_data(self):
        """build_structured_categories returns proper category list"""
        proc = ADMETProcessor()
        data = {
            "molecular_weight": 130.19, "logP": -0.36,
            "HIA_Hou": 0.75, "BBB_Martins": 0.96,
            "hERG": 0.1, "AMES": 0.1,
        }
        cats = proc.build_structured_categories(data)
        assert len(cats) >= 3  # Physicochemical, Absorption, Toxicity
        assert cats[0]["name"] == "Physicochemical"
        assert any(p["key"] == "molecular_weight" for p in cats[0]["properties"])
    
    def test_empty_data_returns_empty(self):
        proc = ADMETProcessor()
        cats = proc.build_structured_categories({"_engine": "test"})
        assert cats == []
    
    def test_status_matches_interpretation(self):
        """Status field aligns with directional scoring"""
        proc = ADMETProcessor()
        data = {"hERG": 0.1, "HIA_Hou": 0.99}
        cats = proc.build_structured_categories(data)
        for cat in cats:
            for prop in cat["properties"]:
                if prop["key"] == "hERG":
                    assert prop["status"] == "success"
                if prop["key"] == "HIA_Hou":
                    assert prop["status"] == "success"

class TestBatchCSVExport:
    def test_batch_csv_format(self):
        proc = ADMETProcessor()
        results = [
            {"index": 1, "smiles": "CCO", "success": True, "engine": "test",
             "categories": [{"name": "Physicochemical", "properties": [
                 {"key": "molecular_weight", "name": "MW", "value": 46.07, "status": "neutral"}
             ]}]},
        ]
        csv = proc.format_batch_csv(results)
        assert "SMILES" in csv
        assert "CCO" in csv
        assert "46.07" in csv
```

### Frontend Build

```bash
cd /Users/mac/Desktop/phhh/frontend && npm run build
```

### Manual Verification

1. **Single molecule analysis**: Enter `CCO` → verify properties show in category cards
2. **Batch SMILES**: Switch to Batch mode → paste 3 SMILES (one per line) → verify all 3 analyzed
3. **SDF upload**: Upload a `.sdf` file → verify molecules parsed and results displayed
4. **Batch CSV export**: Click "Export All CSV" → verify CSV has one row per molecule
5. **Auth token**: Login → navigate to `/lab` → verify no 401 errors in DevTools
6. **Light mode**: Toggle to light mode on Creation Studio and Genetics Hub → verify text readable
