# langchain_supabase_utils.py
import os
from typing import List
from supabase import create_client

try:
    from langchain_community.vectorstores import SupabaseVectorStore
except Exception:
    SupabaseVectorStore = None

def get_supabase_client(url: str, key: str):
    return create_client(url, key)

def get_vectorstore(supabase_client, embedding_fn, table_name: str = "documents"):
    """
    Returns a LangChain-compatible SupabaseVectorStore instance.
    embedding_fn must be an object with embed_documents and embed_query methods.
    """
    if SupabaseVectorStore is None:
        raise ImportError("Install langchain_community (pip install langchain-community).")
    return SupabaseVectorStore(client=supabase_client, embedding=embedding_fn, table_name=table_name)

def upsert_documents(docs: List[dict], supabase_client, embedding_fn):
    """
    docs: list of {"id","source","content","metadata"}
    Computes embeddings locally and upserts rows to Supabase documents table.
    """
    texts = [d["content"] for d in docs]
    embs = embedding_fn.embed_documents(texts)
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
