# app.py
import os
import uuid
from datetime import datetime
from typing import List

import streamlit as st
from supabase import create_client

from ingestion import create_documents_from_uploads, extract_text_from_url
from langchain_supabase_utils import (
    get_supabase_client,
    upsert_documents,
    get_vectorstore,
)
from rag_chain import build_rag_chain
from groq_llm import generate_completion, stream_completion, FAST_MODEL, PREMIUM_MODEL
from prompts import get_rag_enhanced_prompt, pharmacology_system_prompt

# Example
messages = [
    {"role": "system", "content": "You are PharmGPT, a pharmacology tutor."},
    {"role": "user", "content": "Explain beta blockers in simple terms."}
]

# Non-streaming
reply = generate_completion(messages, model=FAST_MODEL)
print("FAST MODE:", reply)

# Streaming
collected = ""
for token in stream_completion(messages, model=PREMIUM_MODEL):
    collected += token
    print(token, end="", flush=True)

    
# --- Page config
st.set_page_config(page_title="PharmGPT — RAG (Groq)", layout="wide", initial_sidebar_state="expanded")

# --- Environment & Supabase client
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error("Please set SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit Secrets.")
    st.stop()

supabase = get_supabase_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Groq model names (set in Streamlit Secrets or env)
GROQ_FAST_MODEL = os.environ.get("GROQ_FAST_MODEL", "gemma2-9b-it")
GROQ_PREMIUM_MODEL = os.environ.get("GROQ_PREMIUM_MODEL", "gemma2-32b")  # replace if you have a different premium model

# --- Sidebar: upload + settings
with st.sidebar:
    st.title("PharmGPT — RAG (Groq)")
    st.markdown("Retrieval-Augmented Generation. RAG is always on.")

    st.subheader("Model tier (Groq)")
    model_choice = st.selectbox("Model tier", [f"Fast: {GROQ_FAST_MODEL}", f"Premium: {GROQ_PREMIUM_MODEL}"])

    st.markdown("---")
    st.subheader("Ingest documents")
    uploaded = st.file_uploader("Upload PDF / DOCX / TXT / MD (multi)", accept_multiple_files=True)
    url_to_ingest = st.text_input("Or paste a URL to ingest (optional)")
    k_retriever = st.slider("Retriever: number of docs (k)", min_value=1, max_value=8, value=4)

    if st.button("Ingest now"):
        docs = []
        if uploaded:
            st.info(f"Processing {len(uploaded)} uploaded files...")
            docs = create_documents_from_uploads(uploaded, chunk_size=500, chunk_overlap=100)
        if url_to_ingest:
            st.info("Fetching URL...")
            try:
                txt = extract_text_from_url(url_to_ingest)
                fake_upload = type("U", (), {
                    "name": url_to_ingest,
                    "read": lambda: txt.encode("utf-8"),
                    "getvalue": lambda: txt.encode("utf-8")
                })()
                docs_from_url = create_documents_from_uploads([fake_upload], chunk_size=500, chunk_overlap=100)
                docs.extend(docs_from_url)
            except Exception as e:
                st.error(f"URL ingest failed: {e}")

        if not docs:
            st.warning("No documents to ingest.")
        else:
            st.info(f"Embedding and upserting {len(docs)} chunks into Supabase (local embeddings). This may take a moment.")
            try:
                res = upsert_documents(docs, supabase_client=supabase)
                st.success(f"Upsert result: {getattr(res, 'status_code', str(res))}")
            except Exception as e:
                st.error(f"Upsert failed: {e}")

# --- Main chat UI (ChatGPT style)
st.title("💊 PharmGPT — RAG Chat")
st.write("Ask questions about pharmacology. Context is retrieved from your uploaded documents (RAG).")

if "conversation_id" not in st.session_state:
    # attempt to create conversation record, but if it fails, fall back to session id
    try:
        conv = supabase.table("conversations").insert({"title": "New conversation", "user_id": None}).execute()
        conv_id = None
        if hasattr(conv, "data") and conv.data:
            conv_id = conv.data[0]["id"]
        elif isinstance(conv, dict) and conv.get("data"):
            conv_id = conv["data"][0]["id"]
        st.session_state["conversation_id"] = conv_id or str(uuid.uuid4())
    except Exception:
        st.session_state["conversation_id"] = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state["messages"] = []  # list of {"role": "user"/"assistant", "content": "...", "ts": ...}

# render conversation using Streamlit chat components (ChatGPT-like)
for msg in st.session_state["messages"]:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    # st.chat_message provides chat bubble UI similar to ChatGPT
    with st.chat_message(role):
        st.markdown(content)

# input
user_input = st.chat_input("Ask PharmGPT a question about pharmacology...")
if user_input:
    # show user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state["messages"].append({"role": "user", "content": user_input, "ts": datetime.utcnow().isoformat()})
    try:
        supabase.table("messages").insert([{
            "conversation_id": st.session_state["conversation_id"],
            "sender": "user",
            "content": user_input
        }]).execute()
    except Exception:
        # non-fatal; continue
        pass

    # Build retriever from Supabase vectorstore
    try:
        vectorstore = get_vectorstore(supabase_client=supabase)
        retriever = vectorstore.as_retriever(search_kwargs={"k": k_retriever})
    except Exception as e:
        st.warning(f"Vectorstore init error: {e}")
        retriever = None

    # choose Groq model
    model_name = GROQ_FAST_MODEL if model_choice.startswith("Fast") else GROQ_PREMIUM_MODEL
    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY not set in Streamlit secrets. Set it and reload.")
    llm = GroqChat(model=model_name, api_key=GROQ_API_KEY)

    # Always-on RAG: retrieve context first
    retrieved_context = ""
    source_docs = []
    if retriever:
        try:
            docs = retriever.get_relevant_documents(user_input)
            # combine top docs into a single context string (with small separators)
            ctx_pieces = []
            for d in docs:
                pieces = []
                md = getattr(d, "metadata", None) or (d.get("metadata") if isinstance(d, dict) else {})
                src = md.get("source") if isinstance(md, dict) else None
                pieces.append(f"Source: {src or md.get('filename') or 'uploaded_doc'}")
                content = getattr(d, "page_content", d.get("content", "")) if d else ""
                pieces.append(content)
                ctx_pieces.append("\n".join(pieces))
            retrieved_context = "\n\n---\n\n".join(ctx_pieces)
            source_docs = docs
        except Exception as e:
            st.warning(f"Retriever failed: {e}")

    # build system prompt with context
    system_prompt = get_rag_enhanced_prompt(user_question=user_input, context=retrieved_context)

    # streaming response into assistant bubble
    with st.chat_message("assistant"):
        assistant_placeholder = st.empty()
        collected = ""
        try:
            # stream chunks from Groq wrapper
            messages_for_model = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ]
            for chunk in llm.stream_chat(messages_for_model):
                collected += chunk
                assistant_placeholder.markdown(collected + "▌")
            # final render
            assistant_placeholder.markdown(collected)
        except Exception as e:
            assistant_placeholder.markdown(f"Generation failed: {e}")

    # store assistant message
    st.session_state["messages"].append({"role": "assistant", "content": collected, "ts": datetime.utcnow().isoformat()})
    try:
        supabase.table("messages").insert([{
            "conversation_id": st.session_state["conversation_id"],
            "sender": "assistant",
            "content": collected
        }]).execute()
    except Exception:
        pass

    # store last sources in session so the sidebar or other UI can show them
    st.session_state["last_sources"] = source_docs

# Sidebar showing source snippets
with st.sidebar.expander("Last RAG Sources (top k)", expanded=False):
    last_sources = st.session_state.get("last_sources", [])
    if not last_sources:
        st.write("No sources retrieved yet.")
    else:
        for i, d in enumerate(last_sources):
            md = getattr(d, "metadata", None) or (d.get("metadata") if isinstance(d, dict) else {})
            title = md.get("source") or md.get("filename") or f"doc-{i+1}"
            content = getattr(d, "page_content", d.get("content", "")) if d else ""
            st.markdown(f"**{title}** — chunk {md.get('chunk_index','?')}")
            st.text(content[:600] + ("..." if len(content) > 600 else ""))

# small note / credits
st.markdown("---")
st.markdown("RAG is always on. Model: Groq (configured via `GROQ_FAST_MODEL` / `GROQ_PREMIUM_MODEL`). Embeddings: sentence-transformers (all-MiniLM-L6-v2).")
