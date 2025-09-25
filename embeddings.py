# embeddings.py
# Provides a simple sentence-transformers wrapper compatible with LangChain's expected interface.

import os
from typing import List
from sentence_transformers import SentenceTransformer

_MODEL = None

def get_sentence_transformer(model_name: str = None):
    global _MODEL
    if _MODEL is None:
        model_name = model_name or os.environ.get("ST_EMBEDDINGS_MODEL", "all-MiniLM-L6-v2")
        _MODEL = SentenceTransformer(model_name)
    return _MODEL

class SentenceTransformersEmbeddingWrapper:
    def __init__(self, model_name: str = None):
        self.model = get_sentence_transformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        embs = self.model.encode(texts, convert_to_numpy=False)
        return [list(e) for e in embs]

    def embed_query(self, text: str) -> List[float]:
        embs = self.model.encode([text], convert_to_numpy=False)
        return list(embs[0])

def get_embeddings():
    return SentenceTransformersEmbeddingWrapper()
