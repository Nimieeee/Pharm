# Benchside UI/UX Strategy: Chat vs. Dedicated Pages

> **Vision**: Maintaining the "AI as the hands, User as the architect" philosophy by providing high-density workspaces for complex scientific tasks while keeping the chat interface for fluid research.

## 🏛️ The Three-Pillar Architecture

We propose moving beyond a "pure chat" interface into a hybrid model where specialized hubs handle high-density data.

### 1. The Real-Time Chat (Base)
**Home for**: Transient research, brainstorming, and quick lookups.
- **Mermaid Diagrams**: Visual explanations of AI responses.
- **Citations/BibTeX**: Contextual evidence for claims.
- **Triggering**: All specialized "Hub" workflows start here.

### 2. The Genetics Dashboard (`/genetics`)
**Home for**: Persistent patient/target genomic data.
- **PharmGx Reports**: 100+ drug-gene interactions, severity heatmaps, and historical tracking.
- **GWAS Deep Dive**: Multi-database variant mapping with interactive genomic browsers.
- **Value**: High density of data that requires 100% viewport width and persistent state.

### 3. The Molecular Lab (`/lab`)
**Home for**: Cheminformatics and predictive modeling.
- **ADMET Analysis**: Interactive dashboard for 119 endpoints, side-by-side molecule comparison.
- **PubMed Explorer**: High-density literature review with LLM-powered synthesis of search clusters. [LLM Needed]
- **DDI Engine**: Complex multi-drug interaction mapping with LLM-guided clinical alternatives. [LLM Needed]
- **Structure Editing**: SMILES/SDF manipulation and SVG rendering gallery.
- **Value**: Specialized tools (RDKit, MedChem) require dedicated layouts for comparative analysis.

### 4. The Creation Studio (`/studio`)
**Home for**: Content construction (Slides & Documents).
- **Outline Editor**: Drag-and-drop hierarchy management.
- **Prose/Slide Editor**: Focused writing/designing mode (Warp mode).
- **Value**: Creative tasks involve frequent switching between "Structure" and "Content" which is cumbersome in chat.

---

## 📊 Feature Categorization Record

| Feature | Primary Hub | LLM Integration? | Why? |
|---------|-------------|------------------|------|
| **Mermaid Charts** | **Chat** | Core | Visual aid for message context. |
| **Citation Manager** | **Chat** | Light | Metadata parsing for claims. |
| **PubMed Search** | **Lab** | High | Needs synthesis across 10-20 papers. |
| **DDI Engine** | **Lab** | Medium | Needs clinical logic for alternatives. |
| **GWAS Lookup** | **Genetics** | Medium | Needs trait-to-variant synergy logic. |
| **PharmGx Report** | **Genetics** | High | Needs patient-friendly interpretation. |
| **Slide Generator** | **Studio** | Core | Heavy content drafting and layout. |
| **Document Generator**| **Studio** | Core | Structured prose generation. |
| **ADMET Analysis** | **Lab** | Light | Data-heavy; LLM for summary insights. |

---

## 🚀 Transition Strategy: "The Handoff"

We don't want to break the "Chat First" flow. Instead, we use **Handoff Components**:

1. **Trigger**: User asks "Analyze this molecule's ADMET" or "Create a PharmGx report."
2. **Preview**: Chat shows a summary card (DeepResearchUI style) with a "View Full Report" button.
3. **Transition**: Clicking the button opens the **Dedicated Hub** in a non-blocking overlay or a new route, pre-populated with the chat context.

---

**Next Steps**: 
1. Prototype the `/lab` route for the ADMET dashboard.
2. Refine the `DeepResearchUI` to act as a handoff component for the Studio.
