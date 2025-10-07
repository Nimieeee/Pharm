"""
Embeddings Service - Wrapper for HuggingFace Embeddings
Provides backward compatibility while using HuggingFace sentence-transformers
"""

# Import HuggingFace embeddings service
from app.services.hf_embeddings import HuggingFaceEmbeddingsService, embeddings_service as hf_embeddings_service

# Export for backward compatibility
embeddings_service = hf_embeddings_service

# Legacy class name for compatibility
MistralEmbeddingsService = HuggingFaceEmbeddingsService
