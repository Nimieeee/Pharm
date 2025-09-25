# app.py

import os
import streamlit as st
from datetime import datetime, timezone

from langchain_supabase_utils import get_supabase_client, get_vectorstore

from rag_chain import build_rag_chain
from groq_llm import generate_completion_stream, FAST_MODE, PREMIUM_MODE
from prompts import get_rag_enhanced_prompt, pharmacology_system_prompt

# ----------------------------
# App Config
# ----------------------------
st.set_page_config(
    page_title="PharmGPT 💊",
    page_icon="💊",
    layout="wide"
)

# ----------------------------
# Environment
# ----------------------------
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not GROQ_API_KEY:
    st.error("Missing required environment variables.")
    st.stop()

supabase = get_supabase_client(SUPABASE_URL, SUPABASE_ANON_KEY)
from embeddings import get_embeddings

embeddings = get_embeddings()
vectorstore = get_vectorstore(supabase, embeddings)

rag_chain = build_rag_chain(vectorstore, client, model)


# ----------------------------
# Sidebar (Mode Toggle)
# ----------------------------
st.sidebar.title("⚙️ Settings")
mode = st.sidebar.radio(
    "Select Mode",
    options=["⚡ Fast", "💎 Premium"],
    index=0
)

if mode == "⚡ Fast":
    selected_model = FAST_MODE
else:
    selected_model = PREMIUM_MODE

# ----------------------------
# Chat State
# ----------------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": pharmacology_system_prompt}
    ]

# ----------------------------
# Chat UI
# ----------------------------
st.title("💊 PharmGPT")
st.caption("Your AI Pharmacology Assistant with RAG")

# Render chat history
for msg in st.session_state["messages"]:
    if msg["role"] in ["user", "assistant"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Input box
if user_input := st.chat_input("Ask me anything about pharmacology..."):
    # Save user message
    st.session_state["messages"].append({
        "role": "user",
        "content": user_input,
        "ts": datetime.now(timezone.utc).isoformat()
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # Build RAG-enhanced query
    rag_prompt = get_rag_enhanced_prompt(user_input, rag_chain)

    with st.chat_message("assistant"):
        response_container = st.empty()
        collected = ""

        for chunk in generate_completion_stream(
            messages=[{"role": "system", "content": pharmacology_system_prompt}] + rag_prompt,
            model=selected_model
        ):
            collected += chunk
            response_container.markdown(collected)

        # Save assistant reply
        st.session_state["messages"].append({
            "role": "assistant",
            "content": collected,
            "ts": datetime.now(timezone.utc).isoformat()
        })
