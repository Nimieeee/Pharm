# app.py
import os
from datetime import datetime, timezone
from typing import List

import streamlit as st

# Local helpers (assumes these files exist in your repo)
from langchain_supabase_utils import get_supabase_client, get_vectorstore, upsert_documents
from ingestion import create_documents_from_uploads, extract_text_from_url
from embeddings import get_embeddings
from groq_llm import generate_completion_stream, FAST_MODE, PREMIUM_MODE
from prompts import get_rag_enhanced_prompt, pharmacology_system_prompt

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="PharmGPT 💊", layout="wide", initial_sidebar_state="expanded")

# ----------------------------
# Env / Secrets
# ----------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not (SUPABASE_URL and SUPABASE_ANON_KEY and GROQ_API_KEY):
    st.error("Please set SUPABASE_URL, SUPABASE_ANON_KEY and GROQ_API_KEY in environment / Streamlit Secrets.")
    st.stop()

# ----------------------------
# Initialize clients / vectorstore / embeddings
# ----------------------------
try:
    supabase = get_supabase_client(SUPABASE_URL, SUPABASE_ANON_KEY)
except Exception as e:
    st.exception(f"Failed to initialize Supabase client: {e}")
    st.stop()

# embeddings wrapper (sentence-transformers CPU)
try:
    embeddings = get_embeddings()
except Exception as e:
    st.exception(f"Failed to initialize embeddings: {e}")
    st.stop()

# vectorstore (LangChain-compatible SupabaseVectorStore)
try:
    vectorstore = get_vectorstore(supabase_client=supabase, embedding_fn=embeddings)
except Exception as e:
    st.exception(f"Failed to initialize vectorstore: {e}")
    st.stop()

# ----------------------------
# Sidebar: settings + ingest
# ----------------------------
with st.sidebar:
    st.title("PharmGPT — RAG (Groq)")
    st.markdown("Upload documents, ingest them, and ask questions. RAG (retrieval) is always-on.")

    st.subheader("Model")
    # toggle: premium on/off (checkbox = toggle-like)
    premium = st.checkbox("Premium Mode", value=False)
    selected_model = PREMIUM_MODE if premium else FAST_MODE
    st.markdown(f"**Active model:** `{selected_model}`")

    st.markdown("---")
    st.subheader("Ingest documents (persist to Supabase)")
    upload_files = st.file_uploader("Upload PDF / DOCX / TXT / MD (multi)", accept_multiple_files=True)
    url_to_ingest = st.text_input("Or paste a URL to ingest (optional)")

    if st.button("Ingest and Upsert"):
        docs_to_upsert = []
        if upload_files:
            st.info(f"Processing {len(upload_files)} uploaded files...")
            try:
                docs_to_upsert += create_documents_from_uploads(upload_files, chunk_size=500, chunk_overlap=100)
                st.success(f"Created {len(docs_to_upsert)} chunks from uploads.")
            except Exception as e:
                st.error(f"Failed to process uploads: {e}")

        if url_to_ingest:
            st.info("Fetching URL...")
            try:
                txt = extract_text_from_url(url_to_ingest)
                fake = type("U", (), {"name": url_to_ingest, "read": lambda: txt.encode("utf-8"), "getvalue": lambda: txt.encode("utf-8")})()
                docs_to_upsert += create_documents_from_uploads([fake], chunk_size=500, chunk_overlap=100)
                st.success(f"Created {len(docs_to_upsert)} chunks from URL.")
            except Exception as e:
                st.error(f"Failed to fetch/parse URL: {e}")

        if docs_to_upsert:
            st.info("Computing embeddings and upserting to Supabase (this runs locally).")
            try:
                upsert_res = upsert_documents(docs_to_upsert, supabase_client=supabase, embedding_fn=embeddings)
                st.success("Upsert finished.")
            except Exception as e:
                st.error(f"Upsert failed: {e}")
        else:
            st.warning("No documents to ingest.")

    st.markdown("---")
    st.subheader("Query options (sidebar)")
    k_retriever = st.slider("Retriever: top k results", min_value=1, max_value=8, value=4)
    st.caption("You can also attach files per query in the chat area (they can be ephemeral or persisted).")

# ----------------------------
# Chat state init
# ----------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": pharmacology_system_prompt}]

if "last_sources" not in st.session_state:
    st.session_state["last_sources"] = []

# ----------------------------
# UI header + history
# ----------------------------
st.title("💊 PharmGPT — RAG Chat")
st.write("Ask about pharmacology. Upload files for this query or persist them to the database. RAG (document retrieval) is always used unless you choose LLM-only.")

# render chat history
for msg in st.session_state["messages"]:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    with st.chat_message(role):
        st.markdown(content)

# ----------------------------
# Query attachments + options (per-query)
# ----------------------------
st.markdown("---")
st.markdown("**Attach files to this query (optional)**")
query_uploads = st.file_uploader("Attach files (PDF/DOCX/TXT/HTML) for this question", accept_multiple_files=True, key="query_uploads")

col1, col2 = st.columns(2)
with col1:
    use_ephemeral = st.checkbox("Use attached files only for this query (do NOT save)", value=True)
with col2:
    persist_uploaded = st.checkbox("Save attached files to Supabase (persist)", value=False)

llm_only = st.checkbox("LLM-only (do NOT retrieve from DB)", value=False)

# ----------------------------
# Chat input and handler
# ----------------------------
user_input = st.chat_input("Ask PharmGPT anything about pharmacology...")
if user_input:
    # record user message
    ts = datetime.now(timezone.utc).isoformat()
    st.session_state["messages"].append({"role": "user", "content": user_input, "ts": ts})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Prepare contexts
    retrieved_context = ""
    ephemeral_context = ""

    # 1) Retrieval from vectorstore (persisted docs) unless llm_only
    docs = []
    if not llm_only:
        retriever = vectorstore.as_retriever(search_kwargs={"k": k_retriever})
        try:
            # prefer new Runnable API
            if hasattr(retriever, "invoke"):
                docs = retriever.invoke(user_input) or []
            elif hasattr(retriever, "get_relevant_documents"):
                docs = retriever.get_relevant_documents(user_input) or []
            else:
                docs = []
        except Exception:
            # fallback to older method if invoke fails
            try:
                docs = retriever.get_relevant_documents(user_input)
            except Exception:
                docs = []

        # convert docs into text pieces safely
        retrieved_texts = []
        for d in docs:
            text = getattr(d, "page_content", None)
            if text is None:
                # some retrievers return dict-like objects
                try:
                    text = d.get("content") or d.get("page_content") or ""
                except Exception:
                    text = str(d)
            retrieved_texts.append(text)
        if retrieved_texts:
            retrieved_context = "\n\n---\n\n".join(retrieved_texts)[:50_000]  # truncate to safe length

    # 2) Handle per-query uploaded files (ephemeral or persist)
    if query_uploads:
        try:
            # chunk uploaded attachments
            uploaded_docs = create_documents_from_uploads(query_uploads, chunk_size=500, chunk_overlap=100)
            if persist_uploaded:
                # upsert and then re-retrieve so they become searchable immediately
                upsert_documents(uploaded_docs, supabase_client=supabase, embedding_fn=embeddings)
                # re-query retriever to include new persisted docs
                retriever = vectorstore.as_retriever(search_kwargs={"k": k_retriever})
                try:
                    docs_new = retriever.invoke(user_input) if hasattr(retriever, "invoke") else retriever.get_relevant_documents(user_input)
                except Exception:
                    docs_new = retriever.get_relevant_documents(user_input)
                # prepend uploaded doc content to retrieved_context (so attached docs have priority)
                new_texts = [getattr(d, "page_content", d.get("content", "")) if hasattr(d, "page_content") or isinstance(d, dict) else str(d) for d in docs_new]
                combined_piece = "\n\n---\n\n".join(new_texts)
                if combined_piece:
                    # place uploaded docs before previous retrieved_context
                    retrieved_context = (combined_piece + "\n\n=== attached docs ===\n\n" + retrieved_context)[:50_000]
            elif use_ephemeral:
                # build ephemeral_context directly from chunked uploaded_docs (top N chunks)
                top_chunks = [d["content"] for d in uploaded_docs][:8]
                ephemeral_context = "\n\n---\n\n".join(top_chunks)[:30_000]
        except Exception as e:
            st.warning(f"Failed to process attached files: {e}")

    # 3) Combine contexts: ephemeral (attached) first, then retrieved
    combined_context = ""
    if ephemeral_context and retrieved_context:
        combined_context = ephemeral_context + "\n\n=== Uploaded docs above ===\n\n" + retrieved_context
    elif ephemeral_context:
        combined_context = ephemeral_context
    else:
        combined_context = retrieved_context

    # 4) Build RAG-enhanced system prompt (falls back to system prompt if no context)
    system_prompt = get_rag_enhanced_prompt(user_question=user_input, context=combined_context)

    # 5) Build messages for the LLM
    messages_for_model = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    # 6) Stream response from Groq LLM
    with st.chat_message("assistant"):
        placeholder = st.empty()
        collected = ""
        try:
            for chunk in generate_completion_stream(messages=messages_for_model, model=selected_model):
                collected += chunk
                # typing cursor for UX
                placeholder.markdown(collected + "▌")
            placeholder.markdown(collected)
        except Exception as e:
            placeholder.markdown(f"Generation error: {e}")
            collected = f"Generation failed: {e}"

    # 7) Save assistant response
    ts2 = datetime.now(timezone.utc).isoformat()
    st.session_state["messages"].append({"role": "assistant", "content": collected, "ts": ts2})

    # 8) Persist last sources for sidebar preview
    last_sources = []
    if ephemeral_context:
        last_sources.append({"source": "Attached (ephemeral)", "content": ephemeral_context[:4000]})
    if not llm_only and docs:
        for d in docs[:k_retriever]:
            meta = getattr(d, "metadata", {}) or (d.get("metadata") if isinstance(d, dict) else {})
            src = meta.get("source") or meta.get("filename") or "persisted_doc"
            content = getattr(d, "page_content", None) or (d.get("content") if isinstance(d, dict) else str(d)) or ""
            last_sources.append({"source": src, "content": content[:4000]})
    st.session_state["last_sources"] = last_sources

# ----------------------------
# Sidebar: Last sources preview
# ----------------------------
with st.sidebar.expander("Last RAG Sources", expanded=False):
    last_sources = st.session_state.get("last_sources", [])
    if not last_sources:
        st.write("No sources retrieved yet.")
    else:
        for s in last_sources:
            st.markdown(f"**{s.get('source', 'doc')}**")
            st.text(s.get("content", "")[:500] + ("..." if len(s.get("content","")) > 500 else ""))

# Footer / notes
st.markdown("---")
st.caption("RAG is always on. Uploaded files may be persisted to Supabase if you chose that option. Models: Groq (Fast/Premium).")
