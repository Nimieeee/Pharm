# langchain_supabase_utils.py
import os
from typing import List

from supabase import create_client

# LangChain imports (SupabaseVectorStore)
try:
    from langchain_community.vectorstores import SupabaseVectorStore
except Exception:
    SupabaseVectorStore = None

# sentence-transformers
from sentence_transformers import SentenceTransformer


# --------- Supabase client ----------
def get_supabase_client(url: str, key: str):
    return create_client(url, key)


def ensure_tables_exist(supabase_client, use_service_role: bool = False):
    """
    Placeholder: run SQL in Supabase SQL editor to create 'documents', 'conversations', 'messages' etc.
    """
    return True


# --------- Local embeddings wrapper that mimics LangChain interface ----------
class SentenceTransformersEmbeddings:
    """
    Minimal wrapper that exposes embed_documents(texts)->List[List[float]] and embed_query(text)->List[float]
    so it can be used as embedding_function by LangChain's SupabaseVectorStore.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # convert_to_numpy=False so we can .tolist() safely
        embs = self._model.encode(texts, convert_to_numpy=False)
        # If the encode returns numpy arrays for each, ensure they are lists
        return [list(e) for e in embs]

    def embed_query(self, text: str) -> List[float]:
        embs = self._model.encode([text], convert_to_numpy=False)
        return list(embs[0])


# --------- Upsert helper (computes embeddings locally and upserts to Supabase) ----------
def upsert_documents(docs: List[dict], supabase_client):
    """
    docs: list of {id, source, content, metadata}
    Compute sentence-transformers embeddings locally and upsert rows into Supabase 'documents' table.
    NOTE: This uses the anon key in the client; for production consider server-side upserts.
    """
    # pick model (dimension for all-MiniLM-L6-v2 = 384)
    model_name = os.environ.get("ST_EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    embedder = SentenceTransformersEmbeddings(model_name=model_name)

    texts = [d["content"] for d in docs]
    embs = embedder.embed_documents(texts)

    rows = []
    for d, emb in zip(docs, embs):
        rows.append(
            {
                "id": d.get("id"),
                "source": d.get("source"),
                "content": d.get("content"),
                "metadata": d.get("metadata", {}),
                "embedding": emb,
            }
        )

    # upsert to Supabase
    res = supabase_client.table("documents").upsert(rows).execute()
    return res


def get_vectorstore(supabase_client):
    """
    Return a LangChain SupabaseVectorStore instance using the local embedding wrapper.
    """
    if SupabaseVectorStore is None:
        raise ImportError("SupabaseVectorStore not available in this LangChain install. Install langchain & langchain-community.")
    model_name = os.environ.get("ST_EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
    embedder = SentenceTransformersEmbeddings(model_name=model_name)
    return SupabaseVectorStore(supabase_client=supabase_client, embedding_function=embedder, table_name="documents")

def ensure_tables_exist(supabase):
    """
    No-op placeholder.
    In production, you should create the tables manually in Supabase SQL Editor.

    Example schema (already shared earlier):
      CREATE TABLE documents (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          content text,
          metadata jsonb
      );

      CREATE TABLE document_embeddings (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          document_id uuid REFERENCES documents(id) ON DELETE CASCADE,
          embedding vector(768)  -- matches sentence-transformers dimension
      );
    """
    return True
