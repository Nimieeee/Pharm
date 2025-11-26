"""
Configuration settings for PharmGPT Backend
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic app settings
    APP_NAME: str = "PharmGPT Backend"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AI Model settings
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    # Embedding settings - Using Mistral embeddings only
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "mistral")  # "sentence-transformers" or "mistral"
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))  # 1024 for Mistral
    
    # Mistral Embeddings settings (using API)
    MISTRAL_EMBED_MODEL: str = os.getenv("MISTRAL_EMBED_MODEL", "mistral-embed")
    MISTRAL_EMBED_DIMENSIONS: int = int(os.getenv("MISTRAL_EMBED_DIMENSIONS", "1024"))
    MISTRAL_MAX_RETRIES: int = int(os.getenv("MISTRAL_MAX_RETRIES", "3"))
    MISTRAL_TIMEOUT: int = int(os.getenv("MISTRAL_TIMEOUT", "30"))
    
    # LangChain settings
    # Optimized chunk size for best quality and speed with Cohere
    LANGCHAIN_CHUNK_SIZE: int = int(os.getenv("LANGCHAIN_CHUNK_SIZE", "1000"))
    LANGCHAIN_CHUNK_OVERLAP: int = int(os.getenv("LANGCHAIN_CHUNK_OVERLAP", "200"))
    LANGCHAIN_CACHE_ENABLED: bool = os.getenv("LANGCHAIN_CACHE_ENABLED", "true").lower() == "true"
    
    # Embedding Cache settings
    EMBEDDING_CACHE_TTL: int = int(os.getenv("EMBEDDING_CACHE_TTL", "3600"))  # 1 hour
    EMBEDDING_CACHE_MAX_SIZE: int = int(os.getenv("EMBEDDING_CACHE_MAX_SIZE", "1000"))
    
    # Migration settings
    EMBEDDING_MIGRATION_ENABLED: bool = os.getenv("EMBEDDING_MIGRATION_ENABLED", "false").lower() == "true"
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
    MIGRATION_PARALLEL_WORKERS: int = int(os.getenv("MIGRATION_PARALLEL_WORKERS", "2"))
    
    # Feature Flags
    USE_MISTRAL_EMBEDDINGS: bool = os.getenv("USE_MISTRAL_EMBEDDINGS", "true").lower() == "true"
    USE_LANGCHAIN_LOADERS: bool = os.getenv("USE_LANGCHAIN_LOADERS", "true").lower() == "true"
    ENABLE_EMBEDDING_CACHE: bool = os.getenv("ENABLE_EMBEDDING_CACHE", "true").lower() == "true"
    FALLBACK_TO_HASH_EMBEDDINGS: bool = os.getenv("FALLBACK_TO_HASH_EMBEDDINGS", "true").lower() == "true"
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Local development
        "http://localhost:5173",  # Vite dev server
        "https://*.netlify.app",  # Netlify deployments
        "https://pharmgpt.netlify.app",  # Production frontend (Netlify)
        "https://*.vercel.app",  # Vercel preview deployments
        "https://pharmgpt.vercel.app",  # Production frontend (Vercel)
        "https://pharmgpt-frontend.vercel.app",  # Alternative Vercel domain
    ]
    
    # Admin settings
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@pharmgpt.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            # Handle comma-separated string from environment variable
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return v
    
    @validator("SUPABASE_URL")
    def validate_supabase_url(cls, v):
        if not v:
            raise ValueError("SUPABASE_URL is required")
        return v
    
    @validator("SUPABASE_ANON_KEY")
    def validate_supabase_key(cls, v):
        if not v:
            raise ValueError("SUPABASE_ANON_KEY is required")
        return v
    
    @validator("MISTRAL_API_KEY")
    def validate_mistral_key(cls, v):
        if not v:
            print("⚠️  Warning: MISTRAL_API_KEY not set - embeddings will use fallback")
        return v
    
    @validator("LANGCHAIN_CHUNK_SIZE")
    def validate_chunk_size(cls, v):
        if v < 100 or v > 8000:
            raise ValueError("LANGCHAIN_CHUNK_SIZE must be between 100 and 8000")
        return v
    
    @validator("LANGCHAIN_CHUNK_OVERLAP")
    def validate_chunk_overlap(cls, v, values):
        chunk_size = values.get("LANGCHAIN_CHUNK_SIZE", 1500)
        if v >= chunk_size:
            raise ValueError("LANGCHAIN_CHUNK_OVERLAP must be less than LANGCHAIN_CHUNK_SIZE")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            # Don't try to JSON parse ALLOWED_ORIGINS, just return the string
            if field_name == 'ALLOWED_ORIGINS':
                return raw_val
            return cls.json_loads(raw_val)


# Global settings instance
settings = Settings()