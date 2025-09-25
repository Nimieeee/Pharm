# PharmGPT — Streamlit RAG skeleton

This repo provides a Streamlit app skeleton for Retrieval-Augmented Generation (RAG) using:
- Supabase Postgres + `pgvector` (vector storage)
- LangChain (chains, retriever)
- Two model tiers:
  - Fast: Groq gemma2-9b-it (via GROQ API)
  - Premium: Qwen qwen3-32b (via OpenRouter)

It supports:
- File ingestion (PDF, DOCX, TXT, MD, HTML, URL)
- Chunking (token-aware using `tiktoken` if installed)
- Embedding generation (OpenAI Embeddings by default)
- Upserting embeddings to Supabase
- Chat interface with optional RAG (conversational retrieval)
- Basic user sign-in / sign-up using Supabase Auth

## Setup

1. Create a Supabase project, enable `pgvector` extension, and run the schema SQL (create `documents`, `conversations`, `messages`) provided earlier in the assistant messages.

2. Add secrets to Streamlit Cloud or local `.env`:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (for client)
- `SUPABASE_SERVICE_ROLE_KEY` (optional — do NOT expose publicly)
- `OPENAI_API_KEY` (for embeddings)
- `GROQ_API_KEY` (for Groq gemma2-9b-it)
- `OPENROUTER_API_KEY` (for qwen3-32b)

3. Install dependencies:
```bash
pip install -r requirements.txt
