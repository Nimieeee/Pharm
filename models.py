"""
AI Model Management for Simple Chatbot
Handles Mistral Small model integration with RAG context and system prompts from prompts.py
"""

import os
from typing import Optional, Dict, Any, List
import streamlit as st
import requests
import json
from prompts import pharmacology_system_prompt


class MistralModel:
    """Mistral Small model implementation with enhanced RAG integration"""
    
    def __init__(self):
        self.api_key = None
        self.model_name = "mistral-small-latest"
        self.api_url = "https://api.mistral.ai/v1/chat/completions"
        self.default_system_prompt = pharmacology_system_prompt
        self._initialize()
    
    def _initialize(self):
        """Initialize Mistral client"""
        try:
            # Try environment variable first
            api_key = os.getenv("MISTRAL_API_KEY")
            
            # Fallback to Streamlit secrets
            if not api_key:
                try:
                    api_key = st.secrets.get("MISTRAL_API_KEY")
                except:
                    pass
            
            # Note: The hardcoded key provided was invalid, user needs to set their own
            # if not api_key:
            #     api_key = "uBrKHYN5sBzrvdTYgel7zyNuPVbnhijvi"  # This key is invalid
            
            if api_key:
                self.api_key = api_key
                st.info("🔑 Mistral API key found - testing connection...")
            else:
                st.error("❌ Mistral API key not found")
                st.info("💡 Please set MISTRAL_API_KEY environment variable or add it to Streamlit secrets")
                
        except Exception as e:
            st.error(f"Error initializing Mistral client: {str(e)}")
    
    def generate_response(self, message: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Generate response using Mistral Small with RAG context"""
        if not self.is_available():
            return "Mistral model is not available. Please check API key configuration."
        
        try:
            # Use custom system prompt or default
            active_system_prompt = system_prompt or self.default_system_prompt
            
            # Build messages array
            messages = [
                {"role": "system", "content": active_system_prompt}
            ]
            
            # Add context if available
            if context and context.strip():
                context_message = f"""**Relevant Context from Uploaded Documents:**

{context}

**End of Context**

Please use this context to provide a comprehensive and detailed answer to the following question. If the context contains relevant information, reference it specifically in your response."""
                messages.append({"role": "user", "content": context_message})
            
            # Add user message
            messages.append({"role": "user", "content": message})
            
            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": 10000,  # Increased for comprehensive responses
                "temperature": 0.7,
                "top_p": 1,
                "stream": False
            }
            
            # Make API request
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return f"Mistral API error: Invalid response format - {result}"
            else:
                # Handle specific error codes
                if response.status_code == 401:
                    return "Mistral API error: Invalid API key. Please check your MISTRAL_API_KEY configuration."
                elif response.status_code == 429:
                    return "Mistral API error: Rate limit exceeded. Please wait and try again."
                elif response.status_code == 400:
                    return "Mistral API error: Bad request. Please check your message format."
                else:
                    error_detail = f"HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        if "detail" in error_data:
                            error_detail = error_data["detail"]
                        elif "error" in error_data:
                            if isinstance(error_data["error"], dict):
                                error_detail = error_data["error"].get("message", f"HTTP {response.status_code}")
                            else:
                                error_detail = str(error_data["error"])
                        else:
                            error_detail = f"HTTP {response.status_code}: {error_data}"
                    except:
                        error_detail = f"HTTP {response.status_code}: {response.text[:200]}"
                    
                    return f"Mistral API error: {error_detail}"
                
        except requests.exceptions.Timeout:
            return "Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return "Connection error. Please check your internet connection."
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if Mistral model is available"""
        return self.api_key is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Mistral model information"""
        return {
            "name": "mistral-small-latest",
            "model": self.model_name,
            "type": "mistral",
            "description": "Advanced AI model optimized for detailed pharmaceutical and scientific responses",
            "provider": "Mistral AI",
            "features": ["RAG Integration", "Custom System Prompts", "Elaborate Responses"]
        }


class ModelManager:
    """Manages Mistral AI model interactions with RAG integration"""
    
    def __init__(self):
        self.model = MistralModel()
    
    def generate_response(self, message: str, context: Optional[str] = None) -> str:
        """
        Generate AI response using Mistral Small with RAG context
        
        Args:
            message: User message
            context: Optional RAG context from documents
            
        Returns:
            AI generated response with context integration
        """
        return self.model.generate_response(
            message=message,
            context=context,
            system_prompt=self.model.default_system_prompt
        )
    
    def is_model_available(self) -> bool:
        """Check if the model is available"""
        return self.model.is_available()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return self.model.get_model_info()
    
    def test_connection(self) -> tuple[bool, str]:
        """Test the API connection"""
        if not self.is_model_available():
            return False, "API key not configured"
        
        try:
            # Simple test with minimal payload
            test_response = self.model.generate_response(
                message="Hello", 
                context=None, 
                system_prompt="You are a helpful assistant."
            )
            if "error" in test_response.lower() or "mistral api error" in test_response.lower():
                return False, test_response
            return True, "Connection successful"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"