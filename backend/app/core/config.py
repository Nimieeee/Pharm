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
    
    @validator("ALLOWED_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()