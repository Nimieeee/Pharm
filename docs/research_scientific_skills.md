# Research Report: Scientific & Medical Skills Audit

After auditing `claude-scientific-skills`, `openclaw-medical-skills`, and `ClawBio`, I have mapped out the "Scientific Hands" we should integrate into Benchside.

## 🧐 Master Audit Findings

### 1. ADMET Analysis (Priority #1)
- **Source**: `openclaw-medical-skills/bio-admet-prediction`
- **Capability**: Uses **ADMETlab 3.0 REST API** to predict 119 endpoints (Absorption, Metabolism, Toxicity) with uncertainty quantification.
- **Local Logic**: Uses **RDKit** for PAINS filtering, Brenk structural alerts, and drug-likeness rules (Lipinski, Veber, Ghose).
- **Benchside Match**: Perfect for the requested "ADMET analysis just like admetlab3".

### 2. Pharmacogenomics (Priority #2)
- **Source**: `ClawBio/pharmgx-reporter` & `clinpgx`
- **Capability**: Mapping 23andMe/AncestryDNA files to 12 major PGx genes (CYP2D6, CYP2C19, etc.) and looking up CPIC guidelines for 51+ drugs.
- **Benchside Match**: Enhances our existing `pharmgx_service.py` with validated clinical rules.

### 3. Population Genetics & GWAS (Priority #3)
- **Source**: `ClawBio/gwas-lookup` & `claude-scientific-skills/gwas-database`
- **Capability**: Federated queries across 9 databases (gnomAD, ClinVar, GTEx, PheWAS).
- **Benchside Match**: Direct upgrade for variant interpretation.

## 🛠️ Selective Integration Strategy ("Top 10 Scientific Hands")

We will "transplant" these modular skills into Benchside's architecture, registering them in our `ServiceContainer`.

| Priority | Skill | Repository | Key Value |
| :--- | :--- | :--- | :--- |
| **1** | `bio-admet-prediction` | OpenClaw | 119 predictive endpoints via ADMETlab 3.0 API |
| **2** | `pytdc` | K-Dense | AI-ready datasets for therapeutics benchmarking |
| **3** | `medchem` | K-Dense | Production-grade medicinal chemistry filtering |
| **4** | `pharmgx-reporter` | ClawBio | CPIC-compliant pharmacogenomics reporting |
| **5** | `gwas-lookup` | ClawBio | Federated variant query across 9 clinical DBs |
| **6** | `scrna-orchestrator` | ClawBio | Automated scRNA-seq analysis (Scanpy) |
| **7** | `lit-synthesizer` | ClawBio | PubMed/bioRxiv synthesis with citation graphs |
| **8** | `rdkit` | K-Dense | Core chemical intelligence (SMILES/Descriptors) |
| **9** | `clinicaltrials` | K-Dense | Structured clinical trial filtering and retrieval |
| **10** | `chembl-database` | K-Dense | Bioactivity and molecule data retrieval |

## 🚀 Next Steps
1. **Plan ADMET Service**: Create an implementation plan specifically for ADMETlab 3.0 integration.
2. **Synchronize Dependencies**: Update `requirements.txt` with `PyTDC`, `medchem`, and `datamol`.
3. **Draft Implementation Plan**: For the first 3 priority skills.

---
*Report by Antigravity*
