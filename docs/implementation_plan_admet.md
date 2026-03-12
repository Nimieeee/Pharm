# Implementation Plan: ADMET Analysis & Scientific Expansion

This plan outlines the integration of ADMETlab 3.0 features and the "Top 10 Scientific Hands" identified from the scientific repository audit.

## User Review Required

> [!IMPORTANT]
> **API Dependency**: ADMETlab 3.0 integration relies on their public REST API (`admetlab3.scbdd.com`). We need to ensure connectivity from the production environment.
> **Dependency Bloat**: Adding `PyTDC`, `medchem`, and `datamol` will increase the backend docker image size.

## Proposed Changes

### [Backend] Pharmacology Services

#### [NEW] [admet_service.py](file:///Users/mac/Desktop/phhh/backend/app/services/admet_service.py)
- Implement `ADMETService` with **ToxMCP robustness patterns**:
    - **Molecule Washing**: Integrate `/api/washmol` to standardize SMILES before analysis.
    - **SVG Rendering**: Integrate `/api/molsvg` for premium molecule visualizations in reports.
    - **Predictive Analytics**: Integrate `/api/admet` for 119 endpoints.
    - **Robustness**: Implement rate-limiting (5 rps), exponential backoff, and endpoint fallback (`/api/admet` -> `/api/single/admet`).
- `calculate_filters(smiles: str)`: Uses RDKit/Medchem for PAINS, Lipinski, and structural alerts.
- `generate_report(smiles: str)`: Consolidates predictions + SVGs into a structured markdown report.
- `export_as_csv(results: dict)`: Formats ADMET endpoints into a downloadable CSV string.

#### [MODIFY] [container.py](file:///Users/mac/Desktop/phhh/backend/app/core/container.py)
- Register `admet_service` in the global `ServiceContainer`.

#### [MODIFY] [requirements.txt](file:///Users/mac/Desktop/phhh/backend/requirements.txt)
- Add `PyTDC`, `medchem`, `datamol`, `deepchem`.

### [Agent] Skill Integration

#### [NEW] [admet-analysis](file:///Users/mac/Desktop/phhh/.agents/skills/admet-analysis/SKILL.md)
- Define tool for molecular ADMET prediction.
- Provide prompt templates for pharmacological reasoning based on ADMET outputs.

#### [NEW] [scientific-hands](file:///Users/mac/Desktop/phhh/.agents/skills/scientific-hands/SKILL.md)
- A meta-skill providing the agent with shortcuts to ChEMBL, PubMed, and GWAS lookup logic.

## Verification Plan

### Automated Tests
- `pytest backend/tests/test_admet_service.py`: Verify API connectivity and RDKit filter logic.
- `python scripts/test_scientific_skills.py`: sanity check for newly registered skills.

### Manual Verification
1. Open Benchside Chat.
2. Input a molecule (e.g., "Aspirin" or "CC(=O)Oc1ccccc1C(=O)O").
3. Ask: "Perform a full ADMET analysis on this molecule."
4. Verify the structured output includes Absorption, Distribution, Metabolism, Excretion, and Toxicity tables.
