"""
AI Model Management for Simple Chatbot
Handles fast (Groq) and premium (OpenAI) model integrations
"""

import os
from typing import Optional, Dict, Any
import streamlit as st
from groq import Groq


class BaseModel:
    """Base interface for AI models"""
    
    def generate_response(self, prompt: str) -> str:
        """Generate response from the model"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if model is available"""
        raise NotImplementedError
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        raise NotImplementedError


class GroqFastModel(BaseModel):
    """Fast model implementation using Groq Gemma2"""
    
    def __init__(self):
        self.client = None
        self.model_name = "gemma2-9b-it"
        self._initialize()
    
    def _initialize(self):
        """Initialize Groq client"""
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                self.client = Groq(api_key=api_key)
        except Exception as e:
            st.error(f"Error initializing Groq client: {str(e)}")
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Groq Fast Model"""
        if not self.is_available():
            return "Groq fast model is not available. Please check API key."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Groq Fast API error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Groq model is available"""
        return self.client is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Groq fast model information"""
        return {
            "name": "Fast Model (Groq Gemma2)",
            "model": self.model_name,
            "type": "fast",
            "description": "Fast, cost-effective responses using Gemma2"
        }


class GroqPremiumModel(BaseModel):
    """Premium model implementation using Groq GPT-OSS"""
    
    def __init__(self):
        self.client = None
        self.model_name = "openai/gpt-oss-20b"
        self._initialize()
    
    def _initialize(self):
        """Initialize Groq client for premium model"""
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                self.client = Groq(api_key=api_key)
        except Exception as e:
            st.error(f"Error initializing Groq premium client: {str(e)}")
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using Groq Premium Model"""
        if not self.is_available():
            return "Groq premium model is not available. Please check API key."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Groq Premium API error: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Groq premium model is available"""
        return self.client is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Groq premium model information"""
        return {
            "name": "Premium Model (Groq GPT-OSS)",
            "model": self.model_name,
            "type": "premium",
            "description": "High-quality, advanced responses using GPT-OSS"
        }


class ModelManager:
    """Manages AI model selection and interactions"""
    
    def __init__(self):
        self.models = {
            "fast": GroqFastModel(),
            "premium": GroqPremiumModel()
        }
        self.current_model = "fast"
    
    def set_model(self, model_type: str):
        """Set the current active model"""
        if model_type in self.models:
            self.current_model = model_type
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def get_current_model(self) -> str:
        """Get the currently active model type"""
        return self.current_model
    
    def generate_response(self, message: str, model_type: Optional[str] = None, context: Optional[str] = None) -> str:
        """
        Generate AI response using selected model
        
        Args:
            message: User message
            model_type: "fast" for Groq Gemma2, "premium" for Groq GPT-OSS (uses current if None)
            context: Optional RAG context to include
            
        Returns:
            AI generated response
        """
        # Use specified model or current model
        selected_model = model_type or self.current_model
        
        if selected_model not in self.models:
            return f"Error: Unknown model type '{selected_model}'"
        
        model = self.models[selected_model]
        
        # Prepare prompt with context if available
        prompt = message
        if context:
            prompt = f"Context: {context}\n\nQuestion: {message}"
        
        return model.generate_response(prompt)
    
    def is_model_available(self, model_type: str) -> bool:
        """Check if a model is available"""
        if model_type in self.models:
            return self.models[model_type].is_available()
        return False
    
    def get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available models"""
        available = {}
        for model_type, model in self.models.items():
            if model.is_available():
                available[model_type] = model.get_model_info()
        return available
    
    def get_model_info(self, model_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        if model_type in self.models:
            return self.models[model_type].get_model_info()
        return None