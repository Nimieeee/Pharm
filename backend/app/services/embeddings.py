"""
Embeddings Service - Wrapper that supports multiple embedding providers
Supports: Cohere (default), Mistral, HuggingFace
"""

import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine which embedding service to use
EMBEDDING_PROVIDER = settings.EMBEDDING_PROVIDER.lower()

if EMBEDDING_PROVIDER == "cohere":
    # Check if Cohere API key is available
    if settings.COHERE_API_KEY:
        logger.info("🚀 Using Cohere embeddings (fast, 100 req/min)")
        from app.services.cohere_embeddings import CohereEmbeddingsService, get_cohere_embeddings_service
        embeddings_service = get_cohere_embeddings_service()
        EmbeddingsService = CohereEmbeddingsService
    else:
        # Fallback to Mistral if Cohere key not set
        logger.warning("⚠️  COHERE_API_KEY not set, falling back to Mistral embeddings (slow)")
        from app.services.hf_embeddings import MistralEmbeddingsService, get_mistral_embeddings_service
        embeddings_service = get_mistral_embeddings_service()
        EmbeddingsService = MistralEmbeddingsService
elif EMBEDDING_PROVIDER == "mistral":
    logger.info("🐌 Using Mistral embeddings (slow, 1 req/sec)")
    from app.services.hf_embeddings import MistralEmbeddingsService, get_mistral_embeddings_service
    embeddings_service = get_mistral_embeddings_service()
    EmbeddingsService = MistralEmbeddingsService
else:
    # Default to Cohere if key available, otherwise Mistral
    if settings.COHERE_API_KEY:
        logger.warning(f"⚠️  Unknown embedding provider '{EMBEDDING_PROVIDER}', defaulting to Cohere")
        from app.services.cohere_embeddings import CohereEmbeddingsService, get_cohere_embeddings_service
        embeddings_service = get_cohere_embeddings_service()
        EmbeddingsService = CohereEmbeddingsService
    else:
        logger.warning(f"⚠️  Unknown embedding provider '{EMBEDDING_PROVIDER}', defaulting to Mistral")
        from app.services.hf_embeddings import MistralEmbeddingsService, get_mistral_embeddings_service
        embeddings_service = get_mistral_embeddings_service()
        EmbeddingsService = MistralEmbeddingsService

# Legacy class name for compatibility
MistralEmbeddingsService = EmbeddingsService
