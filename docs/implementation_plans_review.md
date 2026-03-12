# Implementation Plans Review

**Review Date**: 2026-03-12
**Reviewer**: Claude Opus 4.6
**Reference**: CLAUDE.md (Regression Prevention & Systematic Debugging)

---

## Executive Summary

This review analyzes three implementation plans against CLAUDE.md principles: Service Container pattern, Postprocessing module, TDD requirements, Failure Mode Analysis (FMA), and CoT mandate.

| Plan | ServiceContainer | Postprocessing | TDD/Tests | FMA | CoT Mandate |
|------|-----------------|----------------|-----------|-----|-------------|
| UI Strategy | ❌ Missing | ❌ N/A | ❌ Missing | ❌ Missing | ❌ Missing |
| Local Inference | ❌ Missing | ❌ Missing | ✅ Excellent | ✅ Good | ❌ Missing |
| ADMET | ❌ Missing | ❌ Missing | ⚠️ Partial | ❌ Missing | ❌ Missing |

---

## 1. Implementation Plan: UI Strategy (`implementation_plan_ui_strategy.md`)

### Overview
Proposes Hub-and-Spoke architecture with specialized dashboards (Lab, Genetics, Creation Studio) and a "Handoff" pattern from Chat.

### Strengths
- Clear Hub-and-Spoke architecture pattern
- Well-defined component responsibilities
- Handoff pattern is elegant for specialized workflows

### Critical Issues

#### 1. Missing Service Container Integration
The plan proposes new services but doesn't mention `ServiceContainer`:

```python
# PROPOSED (WRONG - violates CLAUDE.md):
PubMedService.summarize_results()

# REQUIRED PATTERN:
from app.core.container import container

class LabReportService:
    def __init__(self, db):
        self.container = container.initialize(db)
        self.pubmed = self.container.get('pubmed_service')
```

#### 2. No Regression Test Plan
CLAUDE.md requires tests **before** implementation. Missing:
- Test file paths for `LabDashboard.tsx`, `GeneticsDashboard.tsx`, `CreationStudio.tsx`
- Integration tests for Handoff button state passing
- Service tests for synthesis layer

#### 3. Missing Failure Mode Analysis (FMA)
For the Handoff pattern, what could go wrong?

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| State loss on refresh | Medium | High | Use URL params for small data, IndexedDB for large datasets |
| Cross-route state pollution | Medium | Medium | Scope state to conversation ID, use React Context isolation |
| Mobile collapse failure | Medium | High | Add responsive tests, test on 375px viewport |

#### 4. No CoT Retrieval Mentioned
This is complex architecture (new routes, state management, LLM synthesis). CLAUDE.md §5 requires:

```bash
python3 /Users/mac/Desktop/phhh/scripts/cot_retriever.py "Hub and spoke UI architecture with chat handoff"
```

### Required Additions

**File: `tests/regression/test_lab_dashboard.py`**
```python
def test_handoff_button_passes_smiles():
    """Verify clicking 'Open in Lab' populates Lab dashboard with SMILES."""
    pass

def test_pubmed_synthesis_under_3s():
    """Benchmark LLM synthesis time for PubMed (target < 3s)."""
    pass
```

---

## 2. Implementation Plan: Local Inference (`implementation_plan_local_inference.md`)

### Overview
Self-hosted BitNet on AWS Lightsail VPS with intelligent prompt routing based on complexity scoring.

### Strengths
- Exceptionally detailed VPS hardware analysis
- Thorough RAM budget breakdown
- Excellent risk matrix with mitigations
- Proper verification plan with specific test cases

### Critical Issues

#### 1. Service Container Pattern Violation

```python
# PROPOSED in plan (line 115-139):
class PromptComplexityScorer:
    """Scores prompt complexity 0.0-1.0..."""
    def score(self, prompt: str, token_count: int) -> float:
        # ...

# REQUIRED: Must register in ServiceContainer
# File: backend/app/core/container.py
self.register('router_service', lambda: RouterService(self.get('config')))
```

#### 2. Missing Postprocessing Module Integration

The `PromptComplexityScorer` uses regex/keyword matching (lines 118-127):

```python
COMPLEX_SIGNALS = ["review", "synthesize", ...]
```

This should be in `app/services/postprocessing/prompt_analyzer.py`, not in `router_service.py`.

**Correct Structure:**
```python
# File: app/services/postprocessing/prompt_analyzer.py
class PromptAnalyzer:
    COMPLEX_SIGNALS = [...]
    PRIVACY_SIGNALS = [...]

    def score_complexity(self, prompt: str, token_count: int) -> float:
        ...

prompt_analyzer = PromptAnalyzer()  # Singleton

# File: app/services/postprocessing/__init__.py
from .prompt_analyzer import PromptAnalyzer, prompt_analyzer
```

#### 3. LocalInferenceQueue Needs Singleton Registration

```python
# PROPOSED (line 252-269):
class LocalInferenceQueue:
    def __init__(self, max_queue_size: int = 5):
        ...

# REQUIRED: Singleton via ServiceContainer
# In container.py:
self.register('local_queue', lambda: LocalInferenceQueue(max_queue_size=5))
```

#### 4. Provider Enum Extension Needs Container Coordination

Adding `Provider.LOCAL` (line 202-208) affects:
- `multi_provider.py` - already exists
- `MODE_PRIORITIES` configuration - needs environment-aware registration
- `container.py` - provider factory initialization

#### 5. Missing CoT Retrieval

Complex routing logic with escalation rules should use:

```bash
python3 /Users/mac/Desktop/phhh/scripts/cot_retriever.py "Intelligent model routing with complexity scoring"
```

### Exemplary Sections (Follow CLAUDE.md)

The verification plan (lines 389-416) is exemplary with specific test cases:

```bash
# Test router classification logic
pytest tests/test_router_service.py -v
#   - Fast mode + simple prompt → routes to LOCAL (BitNet 2B)
#   - Fast mode + complex prompt → routes to GROQ (Llama 3.1 8B)
#   - Fast mode + local queue full → falls back to GROQ
#   - Detailed mode + privacy prompt → routes to LOCAL (BitNet 8B)
#   - Detailed mode + standard prompt → routes to POLLINATIONS (Sonnet 4.6)
#   - Elite mode → routes to POLLINATIONS (Sonnet 4.6)
#   - Elite mode + Sonnet 4.6 down → falls back to Step 3.5 Flash
```

---

## 3. Implementation Plan: ADMET (`implementation_plan_admet.md`)

### Overview
Integration of ADMETlab 3.0 features with ToxMCP robustness patterns and agent skill integration.

### Strengths
- Clear dependency warning (API, bloat)
- ToxMCP robustness patterns are well-defined
- Skill integration path is documented

### Critical Issues

#### 1. Service Container Missing

```python
# PROPOSED:
class ADMETService:
    def calculate_filters(self, smiles: str): ...

# REQUIRED:
class ADMETService:
    def __init__(self, db):
        self.container = container.initialize(db)
        # If it needs other services:
        # self.some_service = self.container.get('some_service')
```

#### 2. No Postprocessing Module for SVG/Report Processing

`generate_report()` and `export_as_csv()` involve text processing. If any regex/parsing is involved, it belongs in:

```
app/services/postprocessing/admet_processor.py
```

**Example Structure:**
```python
# File: app/services/postprocessing/admet_processor.py
class ADMETProcessor:
    def format_svg_for_report(self, svg: str) -> str:
        """Clean and optimize SVG for markdown embedding."""
        ...

    def format_csv_export(self, results: dict) -> str:
        """Convert ADMET results to CSV string."""
        ...

admet_processor = ADMETProcessor()  # Singleton
```

#### 3. Missing Regression Test File

Plan mentions `pytest backend/tests/test_admet_service.py` but doesn't define:
- Test cases before implementation (TDD violation)
- What constitutes "pass" for RDKit filter logic
- API connectivity mocking (ADMETlab API may be flaky in CI)

**Required Test Structure:**
```python
# File: tests/regression/test_admet_service.py
import pytest
from unittest.mock import Mock, patch

def test_admet_service_washes_molecule():
    """Verify molecule washing before ADMET analysis."""
    pass

def test_admet_service_rate_limiting():
    """Verify exponential backoff on rate limit (5 rps)."""
    pass

def test_admet_service_fallback_to_single_endpoint():
    """Verify fallback from /api/admet to /api/single/admet."""
    pass

@patch('app.services.admet_service.ADMETService._call_api')
def test_admet_service_handles_timeout(mock_call):
    """Verify graceful handling of API timeout."""
    mock_call.side_effect = TimeoutError()
    # Should not raise, should return error dict
    pass
```

#### 4. Dependency Bloat Not Quantified

```python
# Add PyTDC, medchem, datamol, deepchem
```

**Missing Analysis:**
| Package | Disk Size | RAM Impact | Notes |
|---------|-----------|------------|-------|
| PyTDC | ~? MB | ~? MB | Drug discovery datasets |
| medchem | ~? MB | ~? MB | Medicinal chemistry |
| datamol | ~? MB | ~? MB | Molecule manipulation |
| deepchem | ~? MB | ~? MB | Deep learning for chemistry |
| **Total** | **~? GB** | **~? GB** | Must fit in 8GB VPS |

This could conflict with the 8GB RAM budget from the Local Inference plan.

#### 5. No CoT Retrieval

ADMET integration with ToxMCP patterns is complex:

```bash
python3 /Users/mac/Desktop/phhh/scripts/cot_retriever.py "ADMET prediction service with API rate limiting and fallback"
```

---

## Recommended Actions

### Before Any Implementation

#### 1. Run CoT Retrieval (Mandatory per CLAUDE.md §5)

```bash
python3 /Users/mac/Desktop/phhh/scripts/cot_retriever.py "Hub and spoke architecture"
python3 /Users/mac/Desktop/phhh/scripts/cot_retriever.py "Model routing complexity scoring"
python3 /Users/mac/Desktop/phhh/scripts/cot_retriever.py "ADMET service API integration"
```

#### 2. Add ServiceContainer Pattern to All Service Proposals

| Plan | Service | Registration |
|------|---------|--------------|
| UI Strategy | `PubMedService.synthesis` | `container.get('pubmed_service')` |
| Local Inference | `RouterService` | `container.register('router_service', ...)` |
| Local Inference | `LocalInferenceQueue` | `container.register('local_queue', ...)` |
| ADMET | `ADMETService` | `container.register('admet_service', ...)` |

#### 3. Create Regression Tests FIRST (TDD)

```
tests/regression/test_admet_service.py
tests/regression/test_router_service.py
tests/regression/test_local_queue.py
tests/regression/test_lab_dashboard.py
```

#### 4. Add Failure Mode Analysis to Each Plan

Each plan must include a table with:
- 3+ potential failure modes
- Likelihood assessment
- Impact assessment
- Mitigation strategy

#### 5. Quantify Dependency Impact

ADMET dependencies (PyTDC, medchem, etc.) must have:
- Estimated disk size
- Estimated RAM usage
- Compatibility check with 8GB VPS constraint
- Interaction analysis with BitNet memory footprint

---

## CLAUDE.md Compliance Checklist

Before approving these plans for implementation, verify:

- [ ] CoT retrieval executed and output included in plan
- [ ] All new services use `ServiceContainer` pattern
- [ ] Regex/parsing logic placed in `postprocessing/` module
- [ ] Regression tests defined BEFORE implementation
- [ ] Failure Mode Analysis included (3+ failure modes)
- [ ] Dependency bloat quantified (disk/RAM impact)
- [ ] `./run_regression.sh` execution plan documented
- [ ] Pre-commit checklist from CLAUDE.md acknowledged

---

## Conclusion

All three plans have merit but require revision to comply with CLAUDE.md architecture patterns. The most compliant plan is **Local Inference** (good tests, good risk analysis), but it still needs ServiceContainer integration and postprocessing module placement.

**Priority Order for Revision:**
1. **ADMET Plan** - Highest risk (dependency bloat, missing tests)
2. **Local Inference Plan** - Medium risk (good tests, missing container)
3. **UI Strategy Plan** - Lowest immediate risk but missing all CLAUDE.md patterns