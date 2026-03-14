# Gold Standard ADMET V12.1 — ADMET-AI Aligned

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 6 bugs in the ADMET module by aligning with ADMET-AI (Chemprop v2) output format, adding proper directional status logic, and restoring AI interpretation.

**Architecture:** Backend [admet_processor.py](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/admet_processor.py) gets a rewritten [get_interpretation()](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/admet_processor.py#560-652) with directional scoring + full ADMET-AI header mapping. Frontend [StatusBadge](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/StatusBadge.tsx#47-58) becomes icon-only. AI interpretation uses `settings.MISTRAL_API_KEY` via async `httpx`.

**Tech Stack:** Python/FastAPI, React/TypeScript, ADMET-AI (Chemprop v2), Mistral API

---

## Key Insight: We Use ADMET-AI, Not ADMETlab

The local engine returns flat keys like `HIA_Hou`, `Bioavailability_Ma`, `AMES`, etc. with DrugBank percentiles. We should map these to **descriptive** headers matching the ADMET-AI website, not ADMETlab abbreviations.

**ADMET-AI returns these 46 endpoints** (from user's data):

| Internal Key | ADMET-AI Descriptive Header | Category | Direction |
|:---|:---|:---|:---|
| `molecular_weight` | Molecular Weight | Physicochemical | neutral |
| `logP` | LogP | Physicochemical | neutral |
| `hydrogen_bond_acceptors` | Hydrogen Bond Acceptors | Physicochemical | neutral |
| `hydrogen_bond_donors` | Hydrogen Bond Donors | Physicochemical | neutral |
| `Lipinski` | Lipinski Rule of 5 | Physicochemical | benefit |
| `QED` | Quantitative Estimate of Druglikeness | Physicochemical | benefit |
| `stereo_centers` | Stereo Centers | Physicochemical | neutral |
| `tpsa` | Topological Polar Surface Area | Physicochemical | neutral |
| `HIA_Hou` | Human Intestinal Absorption | Absorption | benefit |
| `Bioavailability_Ma` | Oral Bioavailability | Absorption | benefit |
| `Solubility_AqSolDB` | Aqueous Solubility | Absorption | benefit |
| `Lipophilicity_AstraZeneca` | Lipophilicity | Absorption | neutral |
| `HydrationFreeEnergy_FreeSolv` | Hydration Free Energy | Absorption | neutral |
| `Caco2_Wang` | Cell Effective Permeability | Absorption | special |
| `PAMPA_NCATS` | PAMPA Permeability | Absorption | benefit |
| `Pgp_Broccatelli` | P-glycoprotein Inhibition | Absorption | risk |
| `BBB_Martins` | Blood-Brain Barrier Penetration | Distribution | benefit |
| `PPBR_AZ` | Plasma Protein Binding Rate | Distribution | neutral |
| `VDss_Lombardo` | Volume of Distribution at Steady State | Distribution | neutral |
| `CYP1A2_Veith` | CYP1A2 Inhibition | Metabolism | risk |
| `CYP2C19_Veith` | CYP2C19 Inhibition | Metabolism | risk |
| `CYP2C9_Veith` | CYP2C9 Inhibition | Metabolism | risk |
| `CYP2D6_Veith` | CYP2D6 Inhibition | Metabolism | risk |
| `CYP3A4_Veith` | CYP3A4 Inhibition | Metabolism | risk |
| `CYP2C9_Substrate_CarbonMangels` | CYP2C9 Substrate | Metabolism | risk |
| `CYP2D6_Substrate_CarbonMangels` | CYP2D6 Substrate | Metabolism | risk |
| `CYP3A4_Substrate_CarbonMangels` | CYP3A4 Substrate | Metabolism | risk |
| `Half_Life_Obach` | Half Life | Excretion | neutral |
| `Clearance_Hepatocyte_AZ` | Drug Clearance (Hepatocyte) | Excretion | neutral |
| `Clearance_Microsome_AZ` | Drug Clearance (Microsome) | Excretion | neutral |
| `hERG` | hERG Blocking | Toxicity | risk |
| `ClinTox` | Clinical Toxicity | Toxicity | risk |
| `AMES` | Mutagenicity | Toxicity | risk |
| `DILI` | Drug Induced Liver Injury | Toxicity | risk |
| `Carcinogens_Lagunin` | Carcinogenicity | Toxicity | risk |
| `LD50_Zhu` | Acute Toxicity LD50 | Toxicity | neutral |
| `Skin_Reaction` | Skin Reaction | Toxicity | risk |
| `NR-AR` | Androgen Receptor (Full Length) | Toxicity | risk |
| `NR-AR-LBD` | Androgen Receptor (LBD) | Toxicity | risk |
| `NR-AhR` | Aryl Hydrocarbon Receptor | Toxicity | risk |
| `NR-Aromatase` | Aromatase | Toxicity | risk |
| `NR-ER` | Estrogen Receptor (Full Length) | Toxicity | risk |
| `NR-ER-LBD` | Estrogen Receptor (LBD) | Toxicity | risk |
| `NR-PPAR-gamma` | PPAR-γ | Toxicity | risk |
| `SR-ARE` | Antioxidant Response Element | Toxicity | risk |
| `SR-ATAD5` | ATAD5 | Toxicity | risk |
| `SR-HSE` | Heat Shock Factor Response | Toxicity | risk |
| `SR-MMP` | Mitochondrial Membrane Potential | Toxicity | risk |
| `SR-p53` | Tumor Protein p53 | Toxicity | risk |

> [!IMPORTANT]
> **Ototoxicity, Nephrotoxicity, Neurotoxicity, Hematotoxicity** are ADMETlab-only. They do NOT exist in ADMET-AI output. We will NOT add fake endpoints.

---

### Task 1: Rewrite [get_interpretation()](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/admet_processor.py#560-652) with Directional Scoring

**Files:**
- Modify: `backend/app/services/postprocessing/admet_processor.py:560-651`
- Test: [backend/tests/regression/test_admet_service.py](file:///Users/mac/Desktop/phhh/backend/tests/regression/test_admet_service.py)

**Step 1: Write failing tests**

Add to [test_admet_service.py](file:///Users/mac/Desktop/phhh/backend/tests/regression/test_admet_service.py):
```python
class TestDirectionalScoring:
    def test_risk_endpoint_low_is_green(self):
        from app.services.postprocessing.admet_processor import ADMETProcessor
        proc = ADMETProcessor()
        result = proc.get_interpretation("hERG", 0.1)
        assert "✅" in result

    def test_risk_endpoint_high_is_red(self):
        from app.services.postprocessing.admet_processor import ADMETProcessor
        proc = ADMETProcessor()
        result = proc.get_interpretation("Skin_Reaction", 0.96)
        assert "❌" in result

    def test_benefit_endpoint_high_is_green(self):
        from app.services.postprocessing.admet_processor import ADMETProcessor
        proc = ADMETProcessor()
        result = proc.get_interpretation("HIA_Hou", 0.99)
        assert "✅" in result

    def test_pgp_low_is_not_danger(self):
        from app.services.postprocessing.admet_processor import ADMETProcessor
        proc = ADMETProcessor()
        result = proc.get_interpretation("Pgp_Broccatelli", 0.0002)
        assert "❌" not in result
        assert "✅" in result

    def test_physicochemical_is_neutral(self):
        from app.services.postprocessing.admet_processor import ADMETProcessor
        proc = ADMETProcessor()
        result = proc.get_interpretation("molecular_weight", 130.19)
        assert result == ""

    def test_qed_moderate_is_warning(self):
        from app.services.postprocessing.admet_processor import ADMETProcessor
        proc = ADMETProcessor()
        result = proc.get_interpretation("QED", 0.51)
        assert "⚠️" in result
```

**Step 2:** Run tests, verify they FAIL (current logic is broken)

```bash
cd /Users/mac/Desktop/phhh/backend && source .venv/bin/activate && pytest tests/regression/test_admet_service.py::TestDirectionalScoring -v
```

**Step 3:** Rewrite [get_interpretation()](file:///Users/mac/Desktop/phhh/backend/app/services/postprocessing/admet_processor.py#560-652) with this logic:

```python
# Classification: risk endpoints (lower = better)
RISK_ENDPOINTS = {
    "hERG", "AMES", "DILI", "ClinTox", "Carcinogens_Lagunin", "Skin_Reaction",
    "CYP1A2_Veith", "CYP2C9_Veith", "CYP2C19_Veith", "CYP2D6_Veith", "CYP3A4_Veith",
    "CYP2C9_Substrate_CarbonMangels", "CYP2D6_Substrate_CarbonMangels",
    "CYP3A4_Substrate_CarbonMangels", "Pgp_Broccatelli",
    "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER", "NR-ER-LBD",
    "NR-PPAR-gamma", "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53",
}

# Classification: benefit endpoints (higher = better)
BENEFIT_ENDPOINTS = {"HIA_Hou", "Bioavailability_Ma", "BBB_Martins", "PAMPA_NCATS"}

# Scoring: risk → <0.3 green, 0.3-0.7 yellow, ≥0.7 red
#          benefit → ≥0.7 green, 0.3-0.7 yellow, <0.3 red
```

Keep custom thresholds for: QED, Lipinski, Caco2_Wang, Solubility_AqSolDB, PAINS/BRENK/NIH alerts, Clearance, Half-life.

**Step 4:** Run tests, verify PASS

**Step 5:** Commit

---

### Task 2: Update Header Labels to ADMET-AI Descriptive Names

**Files:**
- Modify: `backend/app/services/postprocessing/admet_processor.py:437-492` (header_labels dict)

Replace abbreviated headers with full descriptive names from the mapping table above. For example:
- `"AMES"` → `"Mutagenicity"` (not just "Ames")
- `"Caco2_Wang"` → `"Cell Effective Permeability"` (not "Caco-2")
- `"Skin_Reaction"` → `"Skin Reaction"` (not "Skin Sens.")
- `"NR-Aromatase"` → `"Aromatase"` stays
- `"SR-ARE"` → `"Antioxidant Response Element"` (not just "ARE")
- etc.

---

### Task 3: Fix StatusBadge UI Text Spam

**Files:**
- Modify: [frontend/src/components/shared/StatusBadge.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/shared/StatusBadge.tsx)
- Modify: `frontend/src/components/lab/ADMETPropertyCard.tsx:45`

**StatusBadge.tsx** — Add `showLabel` prop:
```tsx
interface StatusBadgeProps {
  status: StatusType;
  label: string;
  showLabel?: boolean;  // NEW - default true
  className?: string;
}

export default function StatusBadge({ status, label, showLabel = true, className = '' }: StatusBadgeProps) {
  // ... existing config code ...
  return (
    <span title={label} className={...}>
      <Icon className="w-3.5 h-3.5" />
      {showLabel && label}
    </span>
  );
}
```

**ADMETPropertyCard.tsx** line 45 — change to:
```tsx
<StatusBadge status={prop.status} label={prop.status} showLabel={false} />
```

---

### Task 4: Fix AI Interpretation (settings + async httpx)

**Files:**
- Modify: `backend/app/services/admet_service.py:437-525`

Replace [_generate_ai_interpretation()](file:///Users/mac/Desktop/phhh/backend/app/services/admet_service.py#437-526):
1. Remove `import os` / `from mistralai import Mistral` / sync SDK call
2. Use `from app.core.config import settings` for `settings.MISTRAL_API_KEY`
3. Call Mistral REST API via `httpx.AsyncClient`:

```python
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {settings.MISTRAL_API_KEY}"},
        json={
            "model": "mistral-small-latest",
            "messages": [...],
            "max_tokens": 300,
            "temperature": 0.3
        }
    )
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
```

---

### Task 5: Replace Protein Sequences in DrugPool

**Files:**
- Modify: `frontend/src/constants/drugPool.ts:56-57`

Replace:
```ts
{ name: 'Liraglutide', smiles: 'His-Aib-Glt-...', ... }  // INVALID
{ name: 'Semaglutide', smiles: 'Aib-Ser-His-...', ... }  // INVALID
```
With:
```ts
{ name: 'Pioglitazone', smiles: 'O=C1NC(=O)C(CC2=CC=C(OCC3=CC=C(CC4SC=CN4)C=C3)C=C2)N1', year: 1999, class: 'Thiazolidinedione' },
{ name: 'Rosiglitazone', smiles: 'CN(CCOC1=CC=C(CC2SC(=O)NC2=O)C=C1)C1=CC=CC=N1', year: 1999, class: 'Thiazolidinedione' },
```

---

### Task 6: Improve CSV Export with Percentiles and Units

**Files:**
- Modify: `backend/app/services/postprocessing/admet_processor.py:67-211` (format_csv_export)

For the non-legacy (vertical) format, add columns for units and use descriptive headers:
```
Property,Value,DrugBank Percentile,Units
Molecular Weight,130.19,6.44%,Dalton
LogP,-0.36,19.50%,log-ratio
...
```

Map percentile keys (`*_drugbank_approved_percentile`) and add a unit lookup dict.

---

## Verification Plan

### Automated Tests

**Run existing suite first** (baseline — should all pass):
```bash
cd /Users/mac/Desktop/phhh/backend && source .venv/bin/activate && pytest tests/regression/test_admet_service.py -v
```

**Run new directional scoring tests** (Task 1):
```bash
pytest tests/regression/test_admet_service.py::TestDirectionalScoring -v
```

### Manual Verification

1. Run `npm run dev` in `frontend/`, go to Molecular Lab
2. Enter `CN(C)CC(=O)N(C)C` and run analysis
3. **Verify**: No "neutral"/"warning" text — icons only
4. **Verify**: Skin Reaction (0.91+) shows 🔴, hERG (0.03) shows 🟢, HIA (0.75) shows 🟢
5. **Verify**: "Key Insights" has AI-generated interpretation text
6. Click drug suggestions — no structural parsing errors
7. Export CSV → check descriptive headers and DrugBank percentiles
