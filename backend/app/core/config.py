"""
Configuration settings for PharmGPT Backend
"""

import os
from typing import List, Optional, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        # Prevent JSON parsing for string fields
        env_parse_none_str='null',
        extra='ignore'
    )
    
    # Basic app settings
    APP_NAME: str = "PharmGPT Backend"
    VERSION: str = "2.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database settings
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days default
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "180"))  # 6 months default
    
    # AI Model settings
    MISTRAL_API_KEY: str = os.getenv("MISTRAL_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    SERP_API_KEY: str = os.getenv("SERP_API_KEY", "")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    
    # Embedding settings - Using Mistral embeddings only
    # Embedding settings - Using Local Nomic embeddings
    EMBEDDING_PROVIDER: str = os.getenv("EMBEDDING_PROVIDER", "local")  # "local" defaults to Nomic
    EMBEDDING_DIMENSIONS: int = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))  # 768 for Nomic
    
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
    
    # CORS settings - Use str to accept from env, will be converted to list
    ALLOWED_ORIGINS: Union[List[str], str] = "http://localhost:3000,http://localhost:5173,https://pharmgpt.netlify.app,https://pharmgpt.vercel.app,https://pharmgpt-frontend.vercel.app"
    
    # Admin settings
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@pharmgpt.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    # Email settings (Gmail SMTP)
    SMTP_USER: str = os.getenv("SMTP_USER", "noreply.pharmgpt@gmail.com")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD", "")
    RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply.pharmgpt@gmail.com")
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse ALLOWED_ORIGINS from comma-separated string or list"""
        if isinstance(v, str):
            # Handle empty string
            if not v or v.strip() == "":
                return [
                    "http://localhost:3000",
                    "http://localhost:5173",
                    "https://pharmgpt.netlify.app",
                    "https://pharmgpt.vercel.app",
                    "https://pharmgpt-frontend.vercel.app",
                    "https://pharm-eight.vercel.app",
                ]
            # Handle comma-separated string from environment variable
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        # Fallback to defaults
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "https://pharmgpt.netlify.app",
            "https://pharmgpt.vercel.app",
            "https://pharmgpt-frontend.vercel.app",
            "https://pharm-eight.vercel.app",
        ]
    
    @field_validator("SUPABASE_URL", mode="after")
    @classmethod
    def validate_supabase_url(cls, v):
        if not v:
            raise ValueError("SUPABASE_URL is required")
        return v
    
    @field_validator("SUPABASE_ANON_KEY", mode="after")
    @classmethod
    def validate_supabase_key(cls, v):
        if not v:
            raise ValueError("SUPABASE_ANON_KEY is required")
        return v
    
    @field_validator("MISTRAL_API_KEY", mode="after")
    @classmethod
    def validate_mistral_key(cls, v):
        if not v:
            print("⚠️  Warning: MISTRAL_API_KEY not set - embeddings will use fallback")
        return v
    
    @field_validator("LANGCHAIN_CHUNK_SIZE", mode="after")
    @classmethod
    def validate_chunk_size(cls, v):
        if v < 100 or v > 8000:
            raise ValueError("LANGCHAIN_CHUNK_SIZE must be between 100 and 8000")
        return v
    
    @model_validator(mode="after")
    def validate_chunk_overlap(self):
        """Validate chunk overlap is less than chunk size"""
        if self.LANGCHAIN_CHUNK_OVERLAP >= self.LANGCHAIN_CHUNK_SIZE:
            raise ValueError("LANGCHAIN_CHUNK_OVERLAP must be less than LANGCHAIN_CHUNK_SIZE")
        return self


# Global settings instance
settings = Settings()