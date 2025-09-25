# embeddings.py
import os
from typing import List
from sentence_transformers import SentenceTransformer

_MODEL = None

def get_sentence_transformer(model_name: str = None):
    global _MODEL
    if _MODEL is None:
        model_name = model_name or os.environ.get("ST_EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
        # Force CPU device so Streamlit Cloud doesn't choke on meta tensors
        _MODEL = SentenceTransformer(model_name, device="cpu")
    return _MODEL

class SentenceTransformersEmbeddingWrapper:
    def __init__(self, model_name: str = None):
        self.model = get_sentence_transformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embs = self.model.encode(texts, convert_to_numpy=True)  # use numpy for Supabase
        return embs.tolist()

    def embed_query(self, text: str) -> List[float]:
        embs = self.model.encode([text], convert_to_numpy=True)
        return embs[0].tolist()

def get_embeddings():
    return SentenceTransformersEmbeddingWrapper()
