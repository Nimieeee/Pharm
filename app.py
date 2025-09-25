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
    get_embeddings_function,
    ensure_tables_exist,
)
from rag_chain import build_rag_chain
from groq_llm import GroqChat
from openrouter_llm import OpenRouterChat

st.set_page_config(page_title="PharmGPT RAG", layout="wide", initial_sidebar_state="expanded")

# --- Environment / Supabase clients ------------------------------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")  # optional, keep secret

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error("Please set SUPABASE_URL and SUPABASE_ANON_KEY in environment / Streamlit Secrets.")
    st.stop()

supabase = get_supabase_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Ensure DB schema exists (no-op unless you implement service role SQL runner)
ensure_tables_exist(supabase, use_service_role=bool(SUPABASE_SERVICE_ROLE))

# --- Sidebar: auth, settings, ingestion --------------------------------------------
with st.sidebar:
    st.title("PharmGPT — RAG")
    st.write("Retrieval Augmented Generation with Supabase pgvector + LangChain")
    st.markdown("---")

    # Simple email/password auth (server-side sign-in)
    st.subheader("Account")
    if "user" not in st.session_state:
        st.session_state["user"] = None

    if st.session_state["user"] is None:
        email = st.text_input("Email", key="si_email")
        password = st.text_input("Password", type="password", key="si_pw")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Sign in"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    # supabase-py responses vary across versions; try to detect user
                    user = getattr(res, "user", None) or (res.get("data", {}).get("user") if isinstance(res, dict) else None)
                    if user:
                        st.session_state["user"] = user
                        st.success("Signed in")
                        st.experimental_rerun()
                    else:
                        st.warning("Sign-in returned no user; check credentials or Supabase config.")
                except Exception as e:
                    st.error(f"Sign-in failed: {e}")
        with col2:
            if st.button("Sign up"):
                try:
                    supabase.auth.sign_up({"email": email, "password": password})
                    st.info("Sign-up initiated — check your email if you enabled confirmations.")
                except Exception as e:
                    st.error(f"Sign-up failed: {e}")
    else:
        # Display user
        try:
            display_email = st.session_state["user"].get("email") if isinstance(st.session_state["user"], dict) else getattr(st.session_state["user"], "email", "User")
        except Exception:
            display_email = str(st.session_state["user"])
        st.markdown(f"**Signed in:** {display_email}")
        if st.button("Sign out"):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state["user"] = None
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Model & RAG")
    model_choice = st.selectbox("Model tier", ["Fast: gemma2-9b-it (Groq)", "Premium: qwen/qwen3-32b (OpenRouter)"])
    use_rag = st.checkbox("Enable RAG (retriever)", value=True)
    k_retriever = st.slider("Retriever k (number of docs)", min_value=1, max_value=8, value=4)

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
                docs_from_url = create_documents_from_uploads([type("U", (), {"name": url_to_ingest, "read": lambda: txt.encode("utf-8"), "getvalue": lambda: txt.encode("utf-8")})()], chunk_size=500, chunk_overlap=100)
                docs.extend(docs_from_url)
            except Exception as e:
                st.error(f"URL ingest failed: {e}")

        if not docs:
            st.warning("No documents to ingest.")
        else:
            st.info(f"Upserting {len(docs)} chunks to Supabase...")
            with st.spinner("Embedding and upserting..."):
                try:
                    upsert_documents(docs, supabase_client=supabase)
                    st.success(f"Upserted {len(docs)} chunks.")
                except Exception as e:
                    st.error(f"Upsert failed: {e}")

    st.markdown("---")
    st.write("Deploy notes: set SUPABASE_URL, SUPABASE_ANON_KEY, OPENAI_API_KEY (for embeddings), GROQ_API_KEY, OPENROUTER_API_KEY in Streamlit Secrets.")


# --- Main UI: conversation area ----------------------------------------------------
st.title("PharmGPT — RAG Chat")
st.write("Ask questions and optionally retrieve from your uploaded docs.")

# Conversation record in session state
if "conversation_id" not in st.session_state:
    # try to create conversation in DB
    try:
        conv = supabase.table("conversations").insert({"title": "New conversation", "user_id": (st.session_state["user"].get("id") if st.session_state["user"] and isinstance(st.session_state["user"], dict) else None)}).execute()
        # Many supabase-py return shape: res.data or res.get('data')
        conv_id = None
        if hasattr(conv, "data"):
            conv_id = conv.data[0]["id"] if conv.data and isinstance(conv.data, list) else None
        elif isinstance(conv, dict) and conv.get("data"):
            conv_id = conv["data"][0]["id"]
        st.session_state["conversation_id"] = conv_id or str(uuid.uuid4())
    except Exception:
        st.session_state["conversation_id"] = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state["messages"] = []  # list of dicts {"sender","text","ts"}

# Columns: chat + sources
chat_col, src_col = st.columns([3, 1])

with chat_col:
    # Render chat messages with simple bubbles
    for msg in st.session_state["messages"]:
        if msg["sender"] == "user":
            st.markdown(f"<div class='bubble user'><b>You</b><div>{st.markdown(msg['text'], unsafe_allow_html=False)}</div></div>", unsafe_allow_html=True)
            # Simpler rendering below to avoid markup oddities
            st.markdown(f"<div class='bubble user'><b>You</b><pre style='white-space:pre-wrap'>{msg['text']}</pre></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='bubble assistant'><b>Assistant</b><pre style='white-space:pre-wrap'>{msg['text']}</pre></div>", unsafe_allow_html=True)

    # Input box + send
    user_input = st.text_input("Your message", key="user_input")
    if st.button("Send") and user_input:
        # append user message locally & store in DB
        user_msg = {"sender": "user", "text": user_input, "ts": datetime.utcnow().isoformat()}
        st.session_state["messages"].append(user_msg)
        try:
            supabase.table("messages").insert([{"conversation_id": st.session_state["conversation_id"], "sender": "user", "content": user_input}]).execute()
        except Exception:
            pass

        # prepare retriever
        try:
            vectorstore = get_vectorstore(supabase_client=supabase)
            retriever = vectorstore.as_retriever(search_kwargs={"k": k_retriever})
        except Exception as e:
            st.warning(f"Vector store init failed: {e}")
            retriever = None

        # pick LLM wrapper
        if model_choice.startswith("Fast"):
            llm = GroqChat()
        else:
            llm = OpenRouterChat()

        # build chain only if RAG
        answer_text = ""
        source_docs = []
        try:
            if use_rag and retriever:
                chain = build_rag_chain(retriever=retriever, llm=llm, return_source_documents=True)
                # prepare a minimal chat_history from session (list of tuples)
                chat_history = []
                for m in st.session_state["messages"]:
                    # only include last N message pairs if needed
                    chat_history.append((m["sender"], m["text"]))
                # Many ConversationalRetrievalChain variants accept input as {"question":..., "chat_history": ...}
                with st.spinner("Generating (RAG)..."):
                    result = chain({"question": user_input, "chat_history": chat_history})
                    # result shape may be dict or string depending on LC version
                    if isinstance(result, dict):
                        answer_text = result.get("answer") or result.get("response") or str(result)
                        source_docs = result.get("source_documents") or []
                    else:
                        answer_text = str(result)
            else:
                # direct chat
                # messages in OpenAI format
                messages_for_model = [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": user_input}]
                # stream to UI
                placeholder = st.empty()
                collected = ""
                for chunk in llm.stream_chat(messages_for_model):
                    collected += chunk
                    placeholder.markdown(f"**Assistant (streaming)**\n\n{collected}")
                answer_text = collected
        except Exception as e:
            st.error(f"Generation failed: {e}")
            # try a fallback direct chat if chain failed
            try:
                messages_for_model = [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": user_input}]
                answer_text = llm.chat(messages_for_model)
            except Exception as e2:
                answer_text = f"Both chain and direct LLM failed: {e2}"

        # store assistant message
        st.session_state["messages"].append({"sender": "assistant", "text": answer_text, "ts": datetime.utcnow().isoformat()})
        try:
            supabase.table("messages").insert([{"conversation_id": st.session_state["conversation_id"], "sender": "assistant", "content": answer_text}]).execute()
        except Exception:
            pass

        # store sources in session for side panel
        st.session_state["last_sources"] = source_docs
        st.experimental_rerun()

with src_col:
    st.subheader("Sources (RAG)")
    sources = st.session_state.get("last_sources", [])
    if not sources:
        st.info("No sources yet. Use RAG or ingest documents first.")
    else:
        for s in sources:
            # s might be langchain Document or dict
            meta = getattr(s, "metadata", s.get("metadata", {})) if s else {}
            content = getattr(s, "page_content", s.get("content", "")) if s else ""
            st.markdown(f"**{meta.get('source') or meta.get('filename') or 'doc'}** (chunk {meta.get('chunk_index','?')})")
            st.text(content[:400] + ("..." if len(content) > 400 else ""))

# --- CSS for bubbles ---------------------------------------------------------------
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
