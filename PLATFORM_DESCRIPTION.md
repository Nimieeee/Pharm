# PharmGPT — Full Platform Description

## Overview

**PharmGPT** is a **specialized AI-powered pharmacology assistant** designed for researchers, clinicians, and students in the medical and pharmaceutical fields. It combines the conversational intelligence of a Large Language Model (LLM) with advanced document analysis capabilities (RAG) and autonomous research features to provide accurate, evidence-based, and scientifically rigorous answers.

---

## Architecture

The platform is a full-stack web application:

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS, Framer Motion | User interface, real-time chat, dark/light themes |
| **Backend** | Python FastAPI | API layer, business logic, AI orchestration |
| **Database** | Supabase (PostgreSQL + pgvector) | User data, conversations, vector embeddings |
| **AI Core** | Mistral AI API | LLM (chat completions, vision), Embeddings |
| **Search** | PubMed API, Tavily API, Google Scholar (SERP), DuckDuckGo | Research data sources |

---

## Core Features

### 1. AI Chat Interface

A modern, responsive chat UI supporting:

- **Three Modes:**
  - **Fast Mode:** Quick answers using Mistral Small for lower latency.
  - **Detailed Mode:** Comprehensive, elaborate responses for complex questions.
  - **Deep Research Mode:** Autonomous, multi-step literature review (see below).
- **Streaming Responses:** Real-time token-by-token output for a natural conversation feel.
- **Conversation History:** Persistent storage of all chats with the ability to rename, delete, and revisit past conversations.
- **Message Editing & Deletion:** Users can edit their own messages or delete specific messages from a conversation.

### 2. RAG (Retrieval-Augmented Generation) System

Users can upload documents, which are then processed and used to "ground" AI responses with factual, extracted information.

- **Supported File Types:** PDF, DOCX, PPTX, TXT, MD, and images (PNG, JPG, GIF, WebP, TIFF).
- **Document Processing Pipeline:**
  1. **Loaders:** Extract text from various formats (PyPDF2 for PDFs, python-docx for Word, python-pptx for PowerPoints).
  2. **OCR:** For images, Tesseract OCR extracts text.
  3. **Chunking:** Text is split into overlapping chunks (using `RecursiveCharacterTextSplitter` logic) for efficient retrieval.
  4. **Embedding:** Chunks are converted into 1024-dimensional vectors using the **Mistral Embed** API.
  5. **Storage:** Vectors are stored in Supabase's `pgvector` extension with HNSW indexing for fast similarity search.
- **Semantic Search:** When a user asks a question, the system searches for the most relevant document chunks and provides them as context to the LLM.
- **User Isolation:** All document chunks are scoped to a specific `user_id` and `conversation_id`, ensuring privacy and data separation.

### 3. Deep Research Agent (Autonomous Research)

This is the flagship differentiator. When "Deep Research" mode is activated, the platform operates as an **autonomous research agent** inspired by LangGraph-style workflows.

**Workflow (4 Nodes):**

| Step | Node | Description |
|------|------|-------------|
| 1 | **Planner** | The LLM analyzes the user's research question and generates a structured research plan, breaking it into 4 sub-topics with specific keywords and source preferences (PubMed vs. Web). |
| 2 | **Researcher** | For each sub-topic, parallel searches are executed against **PubMed** (NCBI E-utilities), **Google Scholar** (via SERP API), **Tavily** (web search), and **DuckDuckGo**. Findings are validated to filter out garbage results (e.g., "Access Denied" pages). |
| 3 | **Reviewer** | The LLM evaluates if the gathered findings are sufficient to answer the research question. If not, it generates new queries and triggers a **recursive loop** (up to 5 iterations) to fill gaps. |
| 4 | **Writer** | The LLM synthesizes all validated findings into a **comprehensive, academic-style report** with proper Markdown formatting, in-text citations, and a full APA-style reference list. |

**UI Features:**

- A dedicated `DeepResearchUI` component shows real-time progress, including:
  - The overall research strategy/plan overview.
  - Status of each research step.
  - Collected sources with links.
  - The final generated report.

### 4. Data Analysis Workbench

A separate feature for data visualization and analysis.

- **Supported Inputs:** CSV, Excel (XLSX), JSON, TSV, PDF (tables), DOCX (tables).
- **Pipeline (4 Nodes):**
  1. **Style Extractor:** If the user provides a reference image or text description (e.g., "Nature Journal style"), the LLM extracts a visual style configuration (colors, fonts, grids).
  2. **Coder:** The LLM generates Python code (using `matplotlib` and `seaborn`) to create the visualization.
  3. **Executor:** The generated code is executed in a sandboxed subprocess.
  4. **Analyst:** The LLM writes a scientific interpretation of the plotted data.
- **Preset Styles:** Nature Journal, Financial Times, The Economist, Dark Mode, Minimal Scientific.

### 5. Security & Anti-Jailbreak Measures

The backend includes a sophisticated defense system against prompt injection attacks:

- **Hardcoded Identity Constraints:** The system prompt explicitly "locks" the LLM into its "PharmGPT" role, prohibiting identity changes.
- **Keyword-Based Pre-Check:** Before sending user input to the LLM, it's scanned for common injection phrases (e.g., "ignore all previous instructions", "you are now a...").
- **XML Delimiter Defense:** User input and document context are wrapped in `<user_query>` and `<document_context>` XML tags, and special characters are escaped to prevent the LLM from misinterpreting data as instructions.

### 6. User Authentication & Admin Panel

- **JWT-Based Auth:** Secure login/registration with access and refresh tokens.
- **Admin Endpoints:** System health monitoring, user management, and analytics.
- **Support System:** Contact form and ticket management for user assistance.

---

## Frontend Components

| Component | Purpose |
|-----------|---------|
| `ChatInput.tsx` | Message input with mode selector (Fast/Detailed/Deep Research), file upload with drag-and-drop, and a cancel button. |
| `ChatMessage.tsx` | Renders user and assistant messages with Markdown support, code highlighting, and edit/delete actions. |
| `ChatSidebar.tsx` | Lists all conversations, supports search, rename, and delete. |
| `DeepResearchUI.tsx` | Displays the real-time progress and results of the autonomous research agent. |
| `MarkdownRenderer.tsx` | Rich Markdown rendering with support for LaTeX math, tables, and code blocks. |
| `DataWorkbench.tsx` | UI for uploading data files and triggering visualizations with style cloning. |

---

## Backend Services

| Service | File | Purpose |
|---------|------|---------|
| `ai.py` | `app/services/ai.py` | Orchestrates chat responses, manages prompts, and integrates with Mistral API. |
| `rag.py` / `enhanced_rag.py` | `app/services/` | Document processing, embedding generation, and vector search. |
| `deep_research.py` | `app/services/deep_research.py` | The autonomous research agent (Planner, Researcher, Reviewer, Writer nodes). |
| `data_workbench.py` | `app/services/data_workbench.py` | Data visualization agent (Style Extractor, Coder, Executor, Analyst nodes). |
| `mistral_embeddings.py` | `app/services/` | Handles embedding generation with caching and rate-limit handling. |
| `document_loaders.py` | `app/services/` | Extracts text from various file types (PDF, DOCX, PPTX, images). |

---

## Use Cases

1. **Pharmacology Research:** Drug interaction analysis, mechanism of action explanations, clinical trial summaries.
2. **Medical Education:** Pharmacokinetics/pharmacodynamics study, adverse effect profiles, dosing guidelines.
3. **Literature Review:** Automated synthesis of PubMed and Google Scholar papers on a given topic.
4. **Document Q&A:** Upload a research paper and ask specific questions about its content.
5. **Data Visualization:** Upload a CSV of experimental results and generate a publication-ready chart.

---

## Deployment

| Component | Recommended Provider | Notes |
|-----------|---------------------|-------|
| **Frontend** | Vercel / Netlify | Free tier available, easy Next.js deployment. |
| **Backend + Database** | **Oracle Cloud Free Tier** (Self-Hosted) | 4 ARM OCPUs, 24GB RAM, 200GB Storage. Runs Docker Compose with full Supabase stack + your Backend. |

A complete `deployment/` folder with `docker-compose.yml`, `.env.example`, and a step-by-step `README.md` has been prepared for your VPS deployment.

---

## Technology Stack Summary

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS, CSS Variables for theming
- **Animations:** Framer Motion
- **Icons:** Lucide React
- **State Management:** React Context API

### Backend
- **Framework:** FastAPI (Python 3.11)
- **Database Client:** Supabase Python SDK
- **AI APIs:** Mistral AI (Chat, Vision, Embeddings)
- **Document Processing:** PyPDF2, python-docx, python-pptx, Pillow, pytesseract
- **Data Analysis:** pandas, matplotlib, seaborn
- **Authentication:** PyJWT, bcrypt, passlib

### Database
- **Platform:** Supabase (Managed PostgreSQL)
- **Vector Extension:** pgvector with HNSW indexing
- **Tables:** `users`, `conversations`, `messages`, `document_chunks`

### External APIs
- **LLM:** Mistral AI (`mistral-small-latest`, `pixtral-12b-2409`)
- **Embeddings:** Mistral Embed (1024 dimensions)
- **Search:** PubMed (NCBI E-utilities), Tavily, SERP API (Google Scholar), DuckDuckGo

---

## Project Structure

```
phhh/
├── frontend/                   # Next.js frontend application
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   ├── components/        # Reusable UI components
│   │   │   ├── chat/          # Chat-related components
│   │   │   ├── ui/            # Base UI components
│   │   │   └── workbench/     # Data workbench components
│   │   ├── contexts/          # React contexts (Auth, Chat, Sidebar)
│   │   ├── hooks/             # Custom React hooks
│   │   └── lib/               # Utilities and API client
│   ├── public/                # Static assets
│   └── package.json
│
├── backend/                   # FastAPI backend application
│   ├── app/
│   │   ├── api/v1/endpoints/  # API endpoints (auth, chat, admin, workbench)
│   │   ├── core/              # Core configuration (config, database, security)
│   │   ├── models/            # Pydantic models
│   │   └── services/          # Business logic services
│   ├── migrations/            # SQL database migrations
│   ├── scripts/               # Utility scripts
│   ├── main.py                # FastAPI application entry point
│   └── requirements.txt       # Python dependencies
│
├── deployment/                # Self-hosting configuration
│   ├── docker-compose.yml     # Full Supabase + Backend stack
│   ├── .env.example           # Environment variables template
│   └── README.md              # Deployment guide
│
└── docs/                      # Documentation files
    ├── PLATFORM_DESCRIPTION.md  # This file
    ├── API_DOCUMENTATION.md
    ├── DEPLOYMENT.md
    └── ...
```

---

**Built with ❤️ for the pharmacology and medical research community**

*Powered by Next.js, FastAPI, Supabase, Mistral AI, and modern ML technologies*
