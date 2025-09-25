# langchain_supabase_utils.py
import os
from typing import List

from supabase import create_client

# import updated vectorstore location
try:
    from langchain_community.vectorstores import SupabaseVectorStore
except Exception:
    SupabaseVectorStore = None

from embeddings import get_embeddings  # local wrapper

def get_supabase_client(url: str, key: str):
    return create_client(url, key)

def upsert_documents(docs: List[dict], supabase_client):
    """
    Compute embeddings locally (sentence-transformers) and upsert to Supabase `documents` table.
    docs: [{'id','source','content','metadata'}, ...]
    """
    embedder = get_embeddings()
    texts = [d["content"] for d in docs]
    embs = embedder.embed_documents(texts)

    rows = []
    for d, emb in zip(docs, embs):
        rows.append({
            "id": d.get("id"),
            "source": d.get("source"),
            "content": d.get("content"),
            "metadata": d.get("metadata", {}),
            "embedding": emb
        })

    return supabase_client.table("documents").upsert(rows).execute()

def get_vectorstore(supabase_client):
    """
    Return a LangChain-compatible SupabaseVectorStore using the local embedding wrapper.
    """
    if SupabaseVectorStore is None:
        raise ImportError("SupabaseVectorStore from langchain_community is required. Install langchain_community.")
    embedding_fn = get_embeddings()
    return SupabaseVectorStore(supabase_client=supabase_client, embedding_function=embedding_fn, table_name="documents")
