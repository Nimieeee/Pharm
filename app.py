# app.py
import os
import uuid
from datetime import datetime, timezone
from typing import List

import streamlit as st

from langchain_supabase_utils import get_supabase_client, get_vectorstore, upsert_documents
from ingestion import create_documents_from_uploads, extract_text_from_url
from embeddings import get_embeddings
from groq_llm import generate_completion_stream, FAST_MODE, PREMIUM_MODE
from prompts import get_rag_enhanced_prompt, pharmacology_system_prompt

st.set_page_config(page_title="PharmGPT 💊", layout="wide")

# ENV / secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not (SUPABASE_URL and SUPABASE_ANON_KEY and GROQ_API_KEY):
    st.error("Please set SUPABASE_URL, SUPABASE_ANON_KEY, and GROQ_API_KEY in Streamlit secrets.")
    st.stop()

# Supabase + embeddings + vectorstore
supabase = get_supabase_client(SUPABASE_URL, SUPABASE_ANON_KEY)
embeddings = get_embeddings()  # sentence-transformers wrapper
vectorstore = get_vectorstore(supabase_client=supabase, embedding_fn=embeddings)

# Sidebar: ingest + settings
with st.sidebar:
    st.title("PharmGPT — RAG (Groq)")
    st.markdown("Upload documents, ingest them, and ask questions. RAG is always on.")

    st.subheader("Model")
    # Toggle: Fast vs Premium (ChatGPT-like switch)
    mode = st.radio("Mode", options=["⚡ Fast", "💎 Premium"], index=0)
    selected_model = FAST_MODE if mode.startswith("⚡") else PREMIUM_MODE

    st.markdown("---")
    st.subheader("Ingest documents")
    uploaded = st.file_uploader("Upload files (PDF, DOCX, TXT, MD, HTML)", accept_multiple_files=True)
    url_to_ingest = st.text_input("Or enter a URL to ingest (optional)")

    k_retriever = st.slider("Retriever: top k documents", 1, 8, 4)

    if st.button("Ingest now"):
        docs = []
        if uploaded:
            st.info(f"Processing {len(uploaded)} uploaded files...")
            docs = create_documents_from_uploads(uploaded, chunk_size=500, chunk_overlap=100)
        if url_to_ingest:
            st.info("Fetching URL...")
            try:
                txt = extract_text_from_url(url_to_ingest)
                fake = type("U", (), {"name": url_to_ingest, "read": lambda: txt.encode("utf-8"), "getvalue": lambda: txt.encode("utf-8")})()
                docs += create_documents_from_uploads([fake], chunk_size=500, chunk_overlap=100)
            except Exception as e:
                st.error(f"Failed to fetch URL: {e}")

        if not docs:
            st.warning("No docs produced from uploads/URL.")
        else:
            st.info(f"Embedding and upserting {len(docs)} chunks into Supabase (this runs locally).")
            try:
                res = upsert_documents(docs, supabase_client=supabase, embedding_fn=embeddings)
                st.success("Upsert completed.")
            except Exception as e:
                st.error(f"Upsert failed: {e}")

# Chat state
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": pharmacology_system_prompt}]

st.title("💊 PharmGPT — RAG Chat")
st.caption("Ask about pharmacology. Context is retrieved from your uploaded documents (RAG).")

# Render chat history
for m in st.session_state["messages"]:
    if m["role"] in ("user", "assistant"):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# Input and response
user_input = st.chat_input("Ask PharmGPT anything about pharmacology...")
if user_input:
    # save user message
    st.session_state["messages"].append({"role": "user", "content": user_input, "ts": datetime.now(timezone.utc).isoformat()})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Retrieve context (LangChain SupabaseVectorStore retriever)
    retriever = vectorstore.as_retriever(search_kwargs={"k": k_retriever})
    docs = retriever.get_relevant_documents(user_input)
    context = "\n\n---\n\n".join([getattr(d, "page_content", d.get("content", "")) for d in docs])

    # Build RAG-enhanced system/user messages
    system_prompt = get_rag_enhanced_prompt(user_question=user_input, context=context)

    # If get_rag_enhanced_prompt returns a string (as implemented), pass as system or user message:
    messages_for_model = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input}
    ]

    # stream response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        collected = ""
        try:
            for chunk in generate_completion_stream(messages=messages_for_model, model=selected_model):
                collected += chunk
                placeholder.markdown(collected + "▌")
            placeholder.markdown(collected)
        except Exception as e:
            placeholder.markdown(f"Generation error: {e}")
            collected = f"Generation failed: {e}"

    # save assistant
    st.session_state["messages"].append({"role": "assistant", "content": collected, "ts": datetime.now(timezone.utc).isoformat()})

    # store last sources short view in session
    st.session_state["last_sources"] = [{"content": getattr(d, "page_content", d.get("content", "")), "meta": getattr(d, "metadata", d.get("metadata", {}))} for d in docs]

# Sidebar: show last sources
with st.sidebar.expander("Last RAG Sources", expanded=False):
    for i, s in enumerate(st.session_state.get("last_sources", [])[:k_retriever]):
        meta = s.get("meta", {})
        title = meta.get("source") or meta.get("filename") or f"doc-{i+1}"
        st.markdown(f"**{title}**")
        st.text(s.get("content","")[:400] + ("..." if len(s.get("content",""))>400 else ""))
