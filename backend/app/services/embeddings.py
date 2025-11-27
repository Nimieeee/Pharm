"""
Embeddings Service - Using Mistral embeddings
"""

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine which embedding service to use
EMBEDDING_PROVIDER = settings.EMBEDDING_PROVIDER.lower()

if EMBEDDING_PROVIDER == "sentence-transformers" or EMBEDDING_PROVIDER == "local":
    logger.info("⚡ Using Sentence Transformers (local, instant, no rate limits)")
    from app.services.sentence_transformer_embeddings import SentenceTransformerEmbeddingsService, get_sentence_transformer_service
    embeddings_service = get_sentence_transformer_service()
    EmbeddingsService = SentenceTransformerEmbeddingsService
else:
    # Default to Mistral embeddings
    logger.info("🚀 Using Mistral embeddings (1024 dimensions)")
    from app.services.mistral_embeddings import MistralEmbeddingsService, get_mistral_embeddings_service
    embeddings_service = get_mistral_embeddings_service()
    EmbeddingsService = MistralEmbeddingsService

# Legacy class name for compatibility
MistralEmbeddingsService = EmbeddingsService
