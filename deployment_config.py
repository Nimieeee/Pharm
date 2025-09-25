"""
Deployment Configuration for Streamlit Cloud
Handles environment variables, secrets, and deployment-specific settings
"""

import os
import streamlit as st
from typing import Dict, Any, Optional
import logging

class DeploymentConfig:
    """Manages deployment configuration for Streamlit Cloud"""
    
    def __init__(self):
        self.environment = self._get_environment()
        self.config = self._load_config()
        self._setup_logging()
    
    def _get_environment(self) -> str:
        """Determine the current environment"""
        # Check if running on Streamlit Cloud
        if os.environ.get("STREAMLIT_CLOUD"):
            return "production"
        
        # Try to get from Streamlit secrets
        try:
            if hasattr(st, 'secrets') and st.secrets.get("ENVIRONMENT"):
                return st.secrets["ENVIRONMENT"]
        except Exception:
            pass
        
        # Fallback to environment variable
        return os.environ.get("ENVIRONMENT", "development")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables and Streamlit secrets"""
        config = {}
        
        # Required configuration keys
        required_keys = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY", 
            "GROQ_API_KEY"
        ]
        
        # Optional configuration keys with defaults
        optional_keys = {
            "SUPABASE_SERVICE_KEY": None,
            "GROQ_FAST_MODEL": "gemma2-9b-it",
            "GROQ_PREMIUM_MODEL": "qwen/qwen3-32b",
            "APP_SECRET_KEY": "default-secret-key",
            "LOG_LEVEL": "INFO",
            "ST_EMBEDDINGS_MODEL": "all-MiniLM-L6-v2",
            "HEALTH_CHECK_ENABLED": "true",
            "HEALTH_CHECK_TOKEN": None,
            "OPENROUTER_API_KEY": None
        }
        
        # Load required configuration
        missing_keys = []
        for key in required_keys:
            value = self._get_secret_or_env(key)
            if value:
                config[key] = value
            else:
                missing_keys.append(key)
        
        if missing_keys:
            raise ValueError(f"Missing required configuration: {', '.join(missing_keys)}")
        
        # Load optional configuration
        for key, default in optional_keys.items():
            config[key] = self._get_secret_or_env(key) or default
        
        return config
    
    def _get_secret_or_env(self, key: str) -> Optional[str]:
        """Get value from Streamlit secrets or environment variables"""
        try:
            # Try Streamlit secrets first (for cloud deployment)
            if hasattr(st, 'secrets'):
                secrets_dict = dict(st.secrets)
                if key in secrets_dict:
                    return secrets_dict[key]
        except Exception:
            pass
        
        # Fallback to environment variables
        return os.environ.get(key)
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.get("LOG_LEVEL", "INFO").upper())
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler()
            ]
        )
        
        # Reduce noise from third-party libraries in production
        if self.environment == "production":
            logging.getLogger("urllib3").setLevel(logging.WARNING)
            logging.getLogger("requests").setLevel(logging.WARNING)
            logging.getLogger("httpx").setLevel(logging.WARNING)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"
    
    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration"""
        return {
            "url": self.config["SUPABASE_URL"],
            "anon_key": self.config["SUPABASE_ANON_KEY"],
            "service_key": self.config.get("SUPABASE_SERVICE_KEY")
        }
    
    def get_model_config(self) -> Dict[str, str]:
        """Get AI model configuration"""
        return {
            "groq_api_key": self.config["GROQ_API_KEY"],
            "fast_model": self.config["GROQ_FAST_MODEL"],
            "premium_model": self.config["GROQ_PREMIUM_MODEL"],
            "openrouter_api_key": self.config.get("OPENROUTER_API_KEY")
        }
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate configuration and return status"""
        validation_results = {}
        
        # Check database connectivity
        try:
            from supabase import create_client
            supabase = create_client(
                self.config["SUPABASE_URL"],
                self.config["SUPABASE_ANON_KEY"]
            )
            # Simple health check
            supabase.table("users").select("count").limit(1).execute()
            validation_results["database"] = True
        except Exception as e:
            logging.error(f"Database validation failed: {e}")
            validation_results["database"] = False
        
        # Check Groq API
        try:
            from groq import Groq
            client = Groq(api_key=self.config["GROQ_API_KEY"])
            # Simple API check
            models = client.models.list()
            validation_results["groq_api"] = True
        except Exception as e:
            logging.error(f"Groq API validation failed: {e}")
            validation_results["groq_api"] = False
        
        return validation_results

# Global configuration instance
deployment_config = DeploymentConfig()