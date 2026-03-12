# Implementation Plan: Benchside UI Strategy & Scientific Hubs

This plan outlines the transition from a "Chat-Only" interface to a "Chat + Specialized Hubs" architecture to support high-density scientific data and complex creation workflows.

## Proposed Architecture

We will implement a **Hub-and-Spoke** model where the Chat interface acts as the entry point (the "Spoke") and specialized dashboards act as the analysis engines (the "Hubs").

### 1. Molecular Lab Hub (`/lab`) [NEW]
**Purpose**: Centralized dashboard for drug discovery and cheminformatics.

#### [NEW] [LabDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/lab/LabDashboard.tsx)
- **ADMET Viewer**: 119-endpoint grid with radar charts and toxicity alerts.
- **Export Utility**: "Download CSV" button for sharing ADMET raw data.
- **PubMed Explorer**: Columnar view showing search results on the left and LLM-synthesized "Literature Summary" on the right.
- **DDI Mapper**: Matrix-style interaction map for polypharmacy (4+ drugs).
- **Structure Visualization**: RDKit-rendered SVG interactive gallery.

### 2. Genetics Dashboard Hub (`/genetics`) [NEW]
**Purpose**: High-fidelity genomic data visualization and patient risk profiling.

#### [NEW] [GeneticsDashboard.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/genetics/GeneticsDashboard.tsx)
- **PharmGx Visualizer**: Interactive heatmap of 100+ drug-gene interactions with clickable CPIC recommendations.
- **GWAS Context Mapper**: Integrated view of variants, p-values, and trait associations (Open Targets style).

### 3. Creation Studio Hub (`/studio`) [NEW]
**Purpose**: Direct manipulation workspace for generating slides and documents.

#### [NEW] [CreationStudio.tsx](file:///Users/mac/Desktop/phhh/frontend/src/components/studio/CreationStudio.tsx)
- **Warp-Mode Outline Editor**: Tree-view for reordering slide/doc sections.
- **Side-by-Side Preview**: Real-time rendering of PPTX/DOCX drafts.

## The "Handoff" Pattern

Every Chat message containing scientific data will include a **Handoff Component**:
- **Summary**: A high-level LLM-written takeaway.
- **Action Button**: `[Open in Lab]`, `[View Genetics]`, or `[Edit in Studio]`.
- **Context Passing**: The button will pass the session state (SMILES, PMIDs, or Genomic Data) to the route via state or URL parameters.

## LLM Integration Strategy

We will update the backend services to include a **Synthesis Layer**:
- **PubMedService**: Add `summarize_results()` using LLM to group results by therapeutic area.
- **DDIService**: Add `generate_clinical_advice()` to provide safer alternatives for high-severity interactions.
- **PharmGxService**: Add `interpret_genotypes()` to turn raw alleles into conversational patient advice.

## Verification Plan

### Automated Tests
- **Integration Tests**: Verify that clicking a "Handoff" button in Chat correctly populates the Lab dashboard with the provided SMILES.
- **Service Tests**: Benchmark the LLM synthesis time for PubMed (target < 3s).

### Manual Verification
1.  **Mobile Responsibility**: Ensure the `/lab` dashboard collapses into a "List-First" view on mobile.
2.  **State Persistence**: Verify that refreshing the `/lab` page maintains the current molecule being analyzed.
