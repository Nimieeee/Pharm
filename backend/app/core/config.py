"""
Configuration settings for PharmGPT Backend
"""

import os
from typing import List, Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings


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
    
    # Mistral Embeddings settings (using API)
    MISTRAL_EMBED_MODEL: str = os.getenv("MISTRAL_EMBED_MODEL", "mistral-embed")
    MISTRAL_EMBED_DIMENSIONS: int = int(os.getenv("MISTRAL_EMBED_DIMENSIONS", "1024"))
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "1024"))  # Mistral embed dimensions
    MISTRAL_MAX_RETRIES: int = int(os.getenv("MISTRAL_MAX_RETRIES", "3"))
    MISTRAL_TIMEOUT: int = int(os.getenv("MISTRAL_TIMEOUT", "30"))
    
    # LangChain settings
    LANGCHAIN_CHUNK_SIZE: int = int(os.getenv("LANGCHAIN_CHUNK_SIZE", "1500"))
    LANGCHAIN_CHUNK_OVERLAP: int = int(os.getenv("LANGCHAIN_CHUNK_OVERLAP", "300"))
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
        "https://pharmgpt.netlify.app",  # Production frontend
    ]
    
    # Admin settings
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@pharmgpt.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("SUPABASE_URL")
    @classmethod
    def validate_supabase_url(cls, v):
        if not v:
            raise ValueError("SUPABASE_URL is required")
        return v
    
    @field_validator("SUPABASE_ANON_KEY")
    @classmethod
    def validate_supabase_key(cls, v):
        if not v:
            raise ValueError("SUPABASE_ANON_KEY is required")
        return v
    
    @field_validator("MISTRAL_API_KEY")
    @classmethod
    def validate_mistral_key(cls, v):
        if not v:
            print("⚠️  Warning: MISTRAL_API_KEY not set - embeddings will use fallback")
        return v
    
    @field_validator("LANGCHAIN_CHUNK_SIZE")
    @classmethod
    def validate_chunk_size(cls, v):
        if v < 100 or v > 5000:
            raise ValueError("LANGCHAIN_CHUNK_SIZE must be between 100 and 5000")
        return v
    
    @field_validator("LANGCHAIN_CHUNK_OVERLAP")
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        chunk_size = info.data.get("LANGCHAIN_CHUNK_SIZE", 1500)
        if v >= chunk_size:
            raise ValueError("LANGCHAIN_CHUNK_OVERLAP must be less than LANGCHAIN_CHUNK_SIZE")
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# Global settings instance
settings = Settings()