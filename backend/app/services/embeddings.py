"""
Embeddings Service - Wrapper that supports multiple embedding providers
Supports: Sentence Transformers (local, default), Cohere, Mistral
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
elif EMBEDDING_PROVIDER == "cohere":
    # Check if Cohere API key is available
    if settings.COHERE_API_KEY:
        logger.info("🚀 Using Cohere embeddings (fast, 40 req/min trial)")
        from app.services.cohere_embeddings import CohereEmbeddingsService, get_cohere_embeddings_service
        embeddings_service = get_cohere_embeddings_service()
        EmbeddingsService = CohereEmbeddingsService
    else:
        # Fallback to Sentence Transformers if Cohere key not set
        logger.warning("⚠️  COHERE_API_KEY not set, falling back to Sentence Transformers (local)")
        from app.services.sentence_transformer_embeddings import SentenceTransformerEmbeddingsService, get_sentence_transformer_service
        embeddings_service = get_sentence_transformer_service()
        EmbeddingsService = SentenceTransformerEmbeddingsService
elif EMBEDDING_PROVIDER == "mistral":
    logger.info("🐌 Using Mistral embeddings (slow, 1 req/sec)")
    from app.services.hf_embeddings import MistralEmbeddingsService, get_mistral_embeddings_service
    embeddings_service = get_mistral_embeddings_service()
    EmbeddingsService = MistralEmbeddingsService
else:
    # Default to Sentence Transformers (local, no API needed)
    logger.warning(f"⚠️  Unknown embedding provider '{EMBEDDING_PROVIDER}', defaulting to Sentence Transformers (local)")
    from app.services.sentence_transformer_embeddings import SentenceTransformerEmbeddingsService, get_sentence_transformer_service
    embeddings_service = get_sentence_transformer_service()
    EmbeddingsService = SentenceTransformerEmbeddingsService

# Legacy class name for compatibility
MistralEmbeddingsService = EmbeddingsService
