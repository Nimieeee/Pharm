# 🔬 Benchside: Global Product Strategy & 5-Year Roadmap v3

*Updated March 2026 — Incorporates findings from 4 open-source skill repos (869+ skills audited), full codebase analysis, and concrete implementation plans.*

*Sources: [ClawBio](https://github.com/ClawBio/ClawBio) · [K-Dense Scientific Writer](https://github.com/K-Dense-AI/claude-scientific-writer) · [K-Dense Scientific Skills](https://github.com/K-Dense-AI/claude-scientific-skills) · [OpenClaw Medical Skills](https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills) · [deanpeters/Product-Manager-Skills](https://github.com/deanpeters/Product-Manager-Skills)*

---

## 📊 Part 1: Where Benchside Stands Today

### What We Have

| Capability | Status | Differentiator |
|-----------|--------|----------------|
| 4-Node Deep Research Pipeline | ✅ Production | **Strong** — Planner→Researcher→Reviewer→Writer is rare |
| Multi-Provider AI Router | ✅ Production | 4 providers (NVIDIA/Groq/Mistral/Pollinations), 5 modes, health-aware failover |
| CoT Reasoning Store (400k patterns) | ✅ Production | **Unique** — domain-specific reasoning corpus |
| Multi-Format RAG (PDF, DOCX, PPTX, CSV, SDF) | ✅ Production | Baseline |
| DOCX/PDF Export with Mermaid Rendering | ✅ Production | Has Kroki-powered diagram-to-PNG + Benchside watermark |
| Mermaid Auto-Correction (regex) | ✅ Production | 425-line processor + 341-line regression suite |
| Independent Branching (A/B responses) | ✅ Production | Good UX pattern |
| Lab Report Endpoint | ✅ Production | Structured AI-generated reports |
| Multi-Language Support | 🔶 Partial | EN + IT only, needs 8+ |

### What We're Missing (Gaps Ranked by Urgency)

| Gap | Severity | How We Solve It | Source Repo |
|-----|----------|----------------|-------------|
| **Mermaid diagrams appear on every response** | P0 — Annoying | Change system prompt `ai.py:517` from "SHOULD" → "CAN when asked" | Codebase audit |
| **No AI-powered diagram repair** | P0 — Broken UX | New `/mermaid/repair` endpoint using Groq fast model | Codebase audit |
| **No citation management** | P1 — Blocker | CrossRef/PubMed API integration for DOI→BibTeX | K-Dense `citation-management` |
| **No direct database access** | P1 — Catch-up | PubMed E-utilities + RxNorm + GWAS APIs | OpenClaw `pubmed-search`, ClawBio `gwas-lookup` |
| **No drug interaction checker** | P1 — Differentiator | NLM Drug Interaction API (free, no key needed) | OpenClaw `tooluniverse-drug-drug-interaction` |
| **No pharmacogenomics** | P2 — Moon-shot | ClawBio PharmGx Reporter (zero deps, 12 genes, 51 drugs) | ClawBio `pharmgx-reporter` |
| **Export is raw chat dump** | P2 — Polish | Add structured manuscript mode (IMRaD sections) | K-Dense `scientific-writing` |
| **No team collaboration** | P3 — Year 2 | Multi-user workspaces, shared RAG stores | Internal design |
| **No computational science** | P3 — Year 2-3 | HPC job submission, molecular docking | OpenClaw BioOS suite |

### Updated Competitive Position

| Dimension | Benchside (Now) | Benchside (Year 1) | K-Dense Writer | OpenClaw | Elicit |
|-----------|----------------|-------------------|----------------|----------|--------|
| Deep Research | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐ |
| Publication Output | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Database Access | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| Drug Intelligence | ⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| Precision Medicine | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐ |
| UX / Web Interface | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ (CLI) | ⭐⭐ (CLI) | ⭐⭐⭐⭐ |

**Verdict**: By Year 1 end, Benchside becomes the **only platform** combining deep research, publication export, drug interaction checking, and pharmacogenomics in a web interface. K-Dense and OpenClaw have more raw skills but are CLI-only.

---

## 🎯 Part 2: Year 1 Priority Stack (Concrete)

### Phase 1: Immediate Fixes (Week 1)

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| **WS1** | **Mermaid frequency fix** — Change `ai.py:517` from "SHOULD generate" → "CAN generate when explicitly asked" | 30 min | Every response improves |
| **WS2** | **Mermaid AI self-repair** — New `/mermaid/repair` endpoint using Groq/Llama-8B to fix diagrams when regex fails | 4-6 hrs | Broken diagrams auto-fix on refresh |

### Phase 2: Publication Pipeline (Month 1-2)

| # | Feature | Effort | RICE | Source |
|---|---------|--------|------|--------|
| **WS3** | **Manuscript export upgrade** — Add structured mode to existing `export.py` (IMRaD sections, page numbers, headers) | 8-12 hrs | 95 | K-Dense `scientific-writing` |
| **WS4** | **Citation manager** — Extract DOIs/PMIDs from AI output → CrossRef/PubMed API → APA/Vancouver/BibTeX | 12-16 hrs | 88 | K-Dense `citation-management` |

### Phase 3: Database Direct Access (Month 2-3)

| # | Feature | Effort | RICE | Source |
|---|---------|--------|------|--------|
| **WS5** | **PubMed direct search** — NCBI E-utilities integration (no BioPython needed). Structured search results in-chat | 8-12 hrs | 85 | OpenClaw `pubmed-search` |
| **WS6** | **Drug-Drug Interaction engine** — Free NLM/RxNorm APIs. Bidirectional analysis, severity scoring, alternative suggestions | 16-20 hrs | 82 | OpenClaw `tooluniverse-drug-drug-interaction` |

### Phase 4: Precision Medicine (Month 3-4)

| # | Feature | Effort | RICE | Source |
|---|---------|--------|------|--------|
| **WS7** | **GWAS variant lookup** — Federated query across 9 genomic databases (Ensembl, GWAS Catalog, Open Targets, GTEx, FinnGen, UKB, BBJ) | 12-16 hrs | 70 | ClawBio `gwas-lookup` |
| **WS8** | **PharmGx Reporter** — 23andMe/AncestryDNA file → 12-gene, 51-drug personalized report. Zero deps, CPIC-grounded | 16-20 hrs | 65 | ClawBio `pharmgx-reporter` |

**Total Year 1 Engineering**: ~90-120 hours across 4 months

### OpenClaw Skills Catalogued for Future Phases

From the 869-skill OpenClaw repo, these are **deferred** but prioritized for Year 2+:

| Category | Skill Count | Top Skills for Benchside | Year |
|----------|------------|------------------------|------|
| Clinical Trial Design | 5 | `clinical-trial-protocol`, `clinical-trial-matching`, `clinicaltrials-database` | 2 |
| Drug Discovery | 8 | `drug-discovery-search`, `chembl-search`, `drugbank-search`, `drug-target-validation` | 2 |
| Imaging & Pathology | 6 | `pydicom`, `histolab`, `pathml`, `medical-imaging-review` | 3 |
| Lab Automation | 6 | `opentrons-integration`, `benchling-integration`, `protocolsio-integration` | 2 |
| Genomic Databases | 9 | `clinvar-database`, `cosmic-database`, `ensembl-database`, `gene-database` | 2 |
| Protein & Pathway DBs | 18 | `uniprot-database`, `kegg-database`, `pdb-database`, `alphafold-database` | 3 |
| Mental Health | 11 | `crisis-detection-intervention-ai`, `clinical-diagnostic-reasoning` | 3 |
| Regulatory | 2 | `iso-13485-certification`, `hipaa-compliance` | 3 |
| Analyst Personas | 4 | `biologist-analyst`, `chemist-analyst`, `epidemiologist-analyst` | 2 |

---

## 📅 Part 3: The 5-Year Roadmap

### Year 1: "The Research Companion" → Product-Market Fit

#### Q1 (Months 1-3): Foundation Sprint
**Theme**: *Make it exportable, citeable, and queryable*

| Month | Deliverables | Success Metric |
|-------|-------------|----------------|
| **1** | Mermaid frequency fix · AI self-repair · Manuscript export upgrade · Citation manager v1 | ≤2/10 responses have unwanted diagrams · Broken diagrams self-heal · First DOCX manuscript downloads |
| **2** | PubMed direct search · Drug-Drug Interaction engine v1 | Users search PubMed from chat · DDI checks for 2-drug combos return severity + alternatives |
| **3** | GWAS variant lookup · Chemical structure rendering (RDKit SMILES→SVG) | Variant queries return data from 9 databases · Molecules render inline |

**Q1 KPIs**:
- ≥500 manuscript downloads/month
- ≥200 DDI checks/month
- ≥30% of sessions include citation formatting

#### Q2 (Months 4-6): The Writing Lab
**Theme**: *From chat to publication pipeline*

| Deliverable | Details | Source Skill |
|------------|---------|-------------|
| **PharmGx Reporter** | Upload 23andMe → get 12-gene, 51-drug PGx report | ClawBio `pharmgx-reporter` |
| **IMRaD Writer** | Two-stage: outline → prose. User approves structure first | K-Dense `scientific-writing` |
| **Peer Review Scoring** | 7-stage systematic evaluation (methodology, stats, ethics, figures) | K-Dense `peer-review` |
| **Grant Proposal Templates** | NIH R01, NSF CAREER, ERC Starting Grant with section guidance | K-Dense `research-grants` |
| **Clinical Report Writer** | CARE-compliant case reports, SOAP notes, discharge summaries | K-Dense `clinical-reports` |

**Q2 KPIs**:
- ≥100 PharmGx reports/month
- ≥200 grant proposals drafted/month
- Average peer review score ≥7.0/10

#### Q3 (Months 7-9): The Global Researcher
**Theme**: *Scale to worldwide usage*

| Deliverable | Details |
|------------|---------|
| **5 New Languages** | Japanese, Korean, Mandarin, Portuguese, Spanish |
| **Team Workspaces v1** | Shared conversations, @mentions, PI/PostDoc/Student roles |
| **ClinicalTrials.gov Direct** | Search by condition, drug, sponsor, NCT number |
| **Drug Label Search** | Query FDA drug labels via OpenFDA API |
| **Slide Deck Export** | Research thread → PPTX with figures and speaker notes |

#### Q4 (Months 10-12): The Revenue Engine
**Theme**: *Monetize and certify*

| Deliverable | Details |
|------------|---------|
| **Freemium Model** | Free: 10 threads/mo, Fast mode. Pro ($29/mo): Unlimited + Deep Research. Enterprise: Custom |
| **Usage Analytics Dashboard** | Research output metrics, citation counts, team activity |
| **SOC2 Type I Audit** | Begin compliance for enterprise sales |
| **API Access** | RESTful API for programmatic research + export |

**Year 1 Revenue Target**: $50K MRR

---

### Year 2: "The Lab Operating System" → Scale

#### H1: Lab Connectors & Database Expansion
| Deliverable | Source |
|------------|--------|
| Benchling/LabArchives OAuth integration | OpenClaw `benchling-integration` |
| ChEMBL/UniProt/KEGG direct API | OpenClaw database skills |
| Opentrons lab robot integration | OpenClaw `opentrons-integration` |
| ClinVar/COSMIC genomic databases | OpenClaw `clinvar-database`, `cosmic-database` |
| Analyst personas (Biologist, Chemist, Epidemiologist) | OpenClaw analyst skills |

#### H2: Intelligence Layer
| Deliverable | Details |
|------------|---------|
| Shared Lab Memory | Team-wide RAG store for ELNs, SOPs, internal reports |
| Research Knowledge Graph | Visual connections between a team's research topics |
| Project Templates | "Drug Screening Campaign", "Clinical Trial Design", "Literature Review" |
| Slack/Teams Integration | Push notifications and quick-query |

**Year 2 Revenue Target**: $300K MRR

---

### Year 3: "The Regulatory Backbone" → Enterprise

#### H1: Compliance Automation
| Deliverable | Details |
|------------|---------|
| IND/NDA auto-population | Generate regulatory filing drafts from research history |
| Regulatory gap analyzer | "Your submission is missing X, Y, Z for FDA approval" |
| Protocol optimizer | AI-suggested trial designs optimized for power and recruitment |
| SOC2 Type II + HIPAA | Full compliance certifications |
| Medical imaging analysis | Integration of pathology (histolab/PathML) and DICOM (pydicom) |

#### H2: Global Compliance
| Deliverable | Details |
|------------|---------|
| Multi-jurisdiction router | Auto FDA/EMA/PMDA/NMPA/CDSCO adaptation |
| Sovereign cloud options | EU, US, APAC data residency |
| GxP validation | Audit trail, e-signatures, 21 CFR Part 11 |

**Year 3 Revenue Target**: $1.5M MRR

---

### Year 4: "The Dry Lab" → Discovery

#### H1: Computational Discovery
| Deliverable | Source |
|------------|--------|
| HPC job submission (DiffDock, AlphaFold, MD) | OpenClaw BioOS suite |
| Lead scoring dashboard | OpenClaw `drug-discovery-search` |
| In-silico ADMET prediction | OpenClaw `bio-admet-prediction` |
| Protein structure prediction | OpenClaw `alphafold`, `struct-predictor` |

#### H2: Predictive Science
| Deliverable | Details |
|------------|---------|
| Virtual patient cohorts | Simulate clinical trial outcomes before enrollment |
| Target deconvolution | AI-proposed drug targets from phenotypic screening |
| Biomarker discovery pipeline | Multi-omics integration |
| Single-cell analysis | OpenClaw `scanpy`, `scrna-orchestrator` |

**Year 4 Revenue Target**: $5M MRR

---

### Year 5: "The Global Registry" → Platform

#### H1: Open Science
| Deliverable | Details |
|------------|---------|
| Benchside Verified Publishing | AI-reviewed, reproducibility-checked publications |
| Open Research Profiles | Public researcher portfolios |
| Science Credit System | Incentives for dataset contributions |

#### H2: Universal Science
| Deliverable | Details |
|------------|---------|
| Universal Knowledge Graph | Every paper, trial, molecule, gene connected and queryable |
| Benchside API Platform | Third-party developer ecosystem |
| 20+ Languages | Full global coverage |

**Year 5 Revenue Target**: $15M MRR

---

## 🌍 Part 4: Global Expansion Strategy

| Phase | Year | Markets | Strategy | Target |
|-------|------|---------|----------|--------|
| Elite Beachheads | 1 | USA, Switzerland, UK | Free for top 50 universities, 3 pilot labs each | 500 researchers, 5 contracts |
| Pharma Corridor | 2 | Germany, Japan, Singapore | Enterprise sales to pharma R&D, CRO partnerships | 5,000 researchers, 20 contracts |
| Emerging R&D | 3-4 | China, India, Brazil, Korea, Israel | PPP-adjusted pricing, national research council partnerships | 50,000 researchers, 100 contracts |
| Universal Access | 5 | Global (195 countries) | Freemium for developing nations, UN/WHO partnerships | 500,000 researchers |

---

## 🛡️ Part 5: Risk Matrix

| Risk | Severity | Probability | Mitigation |
|------|----------|------------|------------|
| AI hallucination in dosage | 🔴 Critical | Medium | Mandatory disclaimers on DDI/PharmGx output. RxNav cross-check. CPIC-grounded only |
| Data breach (pre-clinical IP) | 🔴 Critical | Low | Zero-trust, SOC2/HIPAA, sovereign cloud |
| Model provider dependency | 🟡 High | High | 4-provider router already built. Add Ollama self-hosted fallback |
| Competitor copies deep research | 🟡 High | High | Speed + CoT corpus moat + ship faster |
| Regulatory pushback on AI | 🟡 High | Medium | "AI-Assisted" not "AI-Decided" positioning. FDA AI workgroup engagement |
| PharmGx liability | 🟡 High | Medium | ClawBio medical disclaimer on every report. "For research/education only" |
| Slow enterprise adoption | 🟠 Medium | Medium | Free academic tier builds bottom-up demand |

---

## 🎯 Part 6: North Star Metrics

| Metric | Year 1 | Year 3 | Year 5 |
|--------|--------|--------|--------|
| Active Researchers | 500 | 50,000 | 500,000 |
| Monthly Research Threads | 5,000 | 500,000 | 10M |
| Manuscripts Exported | 2,000 | 200,000 | 5M |
| DDI Checks Performed | 2,400 | 240,000 | 6M |
| PharmGx Reports Generated | 600 | 60,000 | 1.5M |
| GWAS Lookups | 1,200 | 120,000 | 3M |
| Languages Supported | 9 | 15 | 20+ |
| Enterprise Contracts | 0 | 100 | 1,000 |
| MRR | $50K | $1.5M | $15M |
| Countries Active | 10 | 40 | 195 |

---

## 📦 Part 7: Open Source Skill Library Reference

All 4 repos are cloned to `research/` for implementation reference:

```
research/
├── clawbio/                    # 23 bioinformatics skills
│   └── skills/
│       ├── pharmgx-reporter/   # → WS8 (Month 4)
│       ├── gwas-lookup/        # → WS7 (Month 3)
│       ├── clinpgx/            # → Year 2
│       ├── drug-photo/         # → Year 2
│       └── ...
├── claude-scientific-writer/   # 24 publication skills
│   └── skills/
│       ├── citation-management/ # → WS4 (Month 1-2)
│       ├── scientific-writing/  # → WS3 (Month 1)
│       ├── peer-review/         # → Q2
│       ├── clinical-reports/    # → Q2
│       └── ...
├── claude-scientific-skills/   # 100+ database skills
│   └── scientific-skills/
│       ├── databases/          # ClinVar, COSMIC, UniProt, PubChem...
│       └── ...
└── openclaw-medical-skills/    # 869 skills (superset)
    └── skills/
        ├── pubmed-search/      # → WS5 (Month 2)
        ├── tooluniverse-drug-drug-interaction/ # → WS6 (Month 2-3)
        ├── benchling-integration/ # → Year 2
        ├── opentrons-integration/ # → Year 2
        └── ... (864 more)
```

---

*Prepared by Antigravity — March 2026*
*v3: Incorporates ClawBio, K-Dense, and OpenClaw-Medical-Skills (869 skills audited)*
