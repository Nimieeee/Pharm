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
from groq_llm import GroqChat

st.set_page_config(page_title="PharmGPT (Groq-only)", layout="wide", initial_sidebar_state="expanded")

from embeddings import get_embeddings
embeddings = get_embeddings()


# --------------------------
# Environment & clients
# --------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error("Please set SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit Secrets")
    st.stop()

supabase = get_supabase_client(SUPABASE_URL, SUPABASE_ANON_KEY)
#ensure_tables_exist(supabase)  # no-op placeholder (use SQL editor for schema)

# Groq model envs
GROQ_FAST_MODEL = os.environ.get("GROQ_FAST_MODEL", "gemma2-9b-it")
GROQ_PREMIUM_MODEL = os.environ.get("GROQ_PREMIUM_MODEL", "gemma2-32b")
# API key is required
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.warning("GROQ_API_KEY not set in secrets — generation will fail until provided.")

# --------------------------
# Sidebar: auth / ingest / model
# --------------------------
with st.sidebar:
    st.title("PharmGPT — Groq (Fast & Premium)")
    st.markdown("Upload docs, ingest, then chat. Both modes use Groq models.")

    st.subheader("Model & RAG")
    model_choice = st.selectbox("Model tier", [f"Fast: {GROQ_FAST_MODEL}", f"Premium: {GROQ_PREMIUM_MODEL}"])
    use_rag = st.checkbox("Enable RAG (retriever)", value=True)
    k_retriever = st.slider("Retriever: number of docs (k)", min_value=1, max_value=8, value=4)

    st.markdown("---")
    st.subheader("Ingest documents")
    uploaded = st.file_uploader("Upload PDF / DOCX / TXT / MD (multi)", accept_multiple_files=True)
    url_to_ingest = st.text_input("Or paste a URL to ingest (optional)")

    if st.button("Ingest now"):
        docs = []
        if uploaded:
            st.info(f"Processing {len(uploaded)} uploaded files...")
            docs = create_documents_from_uploads(uploaded, chunk_size=500, chunk_overlap=100)
        if url_to_ingest:
            st.info("Fetching URL...")
            try:
                txt = extract_text_from_url(url_to_ingest)
                fake_upload = type("U", (), {"name": url_to_ingest, "read": lambda: txt.encode("utf-8"), "getvalue": lambda: txt.encode("utf-8")})()
                docs_from_url = create_documents_from_uploads([fake_upload], chunk_size=500, chunk_overlap=100)
                docs.extend(docs_from_url)
            except Exception as e:
                st.error(f"URL ingest failed: {e}")

        if not docs:
            st.warning("No documents to ingest.")
        else:
            st.info(f"Embedding and upserting {len(docs)} chunks into Supabase (local sentence-transformers).")
            try:
                res = upsert_documents(docs, supabase_client=supabase)  # local embeddings computed inside helper
                st.success(f"Upsert response: {getattr(res, 'status_code', str(res))}")
            except Exception as e:
                st.error(f"Upsert failed: {e}")

# --------------------------
# Main chat UI
# --------------------------
st.title("PharmGPT — Groq only (chat)")

if "conversation_id" not in st.session_state:
    try:
        conv = supabase.table("conversations").insert({"title": "New conversation", "user_id": None}).execute()
        conv_id = None
        if hasattr(conv, "data"):
            conv_id = conv.data[0]["id"] if conv.data and isinstance(conv.data, list) else None
        elif isinstance(conv, dict) and conv.get("data"):
            conv_id = conv["data"][0]["id"]
        st.session_state["conversation_id"] = conv_id or str(uuid.uuid4())
    except Exception:
        st.session_state["conversation_id"] = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state["messages"] = []

chat_col, src_col = st.columns([3, 1])

with chat_col:
    # render messages
    for msg in st.session_state["messages"]:
        if msg["sender"] == "user":
            st.markdown(f"<div class='bubble user'><b>You</b><pre style='white-space:pre-wrap'>{msg['text']}</pre></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bubble assistant'><b>Assistant</b><pre style='white-space:pre-wrap'>{msg['text']}</pre></div>", unsafe_allow_html=True)

    user_input = st.text_input("Your message", key="user_input")
    if st.button("Send") and user_input:
        st.session_state["messages"].append({"sender": "user", "text": user_input, "ts": datetime.utcnow().isoformat()})
        # store user message in DB
        try:
            supabase.table("messages").insert([{"conversation_id": st.session_state["conversation_id"], "sender": "user", "content": user_input}]).execute()
        except Exception:
            pass

        # setup retriever
        vectorstore = None
        retriever = None
        try:
            vectorstore = get_vectorstore(supabase_client=supabase)
            retriever = vectorstore.as_retriever(search_kwargs={"k": k_retriever})
        except Exception as e:
            st.warning(f"Vectorstore init error (is embeddings done & table present?): {e}")

        # choose Groq model based on selection
        model_name = GROQ_FAST_MODEL if model_choice.startswith("Fast") else GROQ_PREMIUM_MODEL
        llm = GroqChat(model=model_name, api_key=os.environ.get("GROQ_API_KEY"))

        answer_text = ""
        sources = []
        try:
            if use_rag and retriever:
                chain = build_rag_chain(retriever=retriever, llm=llm, return_source_documents=True)
                # build simple chat_history (list of tuples)
                chat_history = []
                for m in st.session_state["messages"]:
                    chat_history.append((m["sender"], m["text"]))
                with st.spinner("Generating (RAG + Groq)..."):
                    result = chain({"question": user_input, "chat_history": chat_history})
                    if isinstance(result, dict):
                        answer_text = result.get("answer") or result.get("response") or str(result)
                        sources = result.get("source_documents") or []
                    else:
                        answer_text = str(result)
            else:
                # direct Groq call (streaming fallback)
                messages_for_model = [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": user_input}]
                placeholder = st.empty()
                collected = ""
                for chunk in llm.stream_chat(messages_for_model):
                    collected += chunk
                    placeholder.markdown(f"**Assistant (streaming)**\n\n{collected}")
                answer_text = collected
        except Exception as e:
            st.error(f"Generation failed: {e}")
            try:
                answer_text = llm.chat([{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": user_input}])
            except Exception as e2:
                answer_text = f"LLM error: {e2}"

        st.session_state["messages"].append({"sender": "assistant", "text": answer_text, "ts": datetime.utcnow().isoformat()})
        try:
            supabase.table("messages").insert([{"conversation_id": st.session_state["conversation_id"], "sender": "assistant", "content": answer_text}]).execute()
        except Exception:
            pass

        st.session_state["last_sources"] = sources
        st.experimental_rerun()

with src_col:
    st.subheader("Sources")
    sources = st.session_state.get("last_sources", [])
    if not sources:
        st.info("No sources to show. Use RAG and ingest docs first.")
    else:
        for d in sources:
            meta = getattr(d, "metadata", d.get("metadata", {})) if d else {}
            content = getattr(d, "page_content", d.get("content", "")) if d else ""
            st.markdown(f"**{meta.get('source') or meta.get('filename') or 'doc'}** — chunk {meta.get('chunk_index','?')}")
            st.text(content[:400] + ("..." if len(content) > 400 else ""))

# CSS
st.markdown(
    """
    <style>
    .bubble { padding:12px; border-radius:12px; margin:8px 0; font-family: Inter, sans-serif; }
    .user { background:#daf0ff; border:1px solid #90cdf4; }
    .assistant { background:#f7f7fb; border:1px solid #e5e7eb; }
    </style>
    """,
    unsafe_allow_html=True,
)
