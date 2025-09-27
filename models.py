"""
AI Model Management for Simple Chatbot
Handles Mistral Small model integration with RAG context and system prompts from prompts.py
"""

import os
from typing import Optional, Dict, Any, List
import streamlit as st

# Import system prompt from prompts.py
try:
    import prompts
    pharmacology_system_prompt = prompts.pharmacology_system_prompt
except (ImportError, AttributeError):
    # Fallback system prompt if prompts.py is not available
    pharmacology_system_prompt = """You are PharmGPT, an expert pharmacology assistant. Provide detailed, comprehensive, and scientifically accurate responses about pharmaceutical topics, drug interactions, mechanisms of action, and clinical applications. Always provide elaborate and detailed explanations unless specifically asked for brevity."""

try:
    from mistralai import Mistral
except ImportError:
    st.error("❌ mistralai package not installed. Run: pip install mistralai")
    st.stop()


class MistralModel:
    """Mistral Small model implementation with enhanced RAG integration"""
    
    def __init__(self):
        self.client = None
        self.model_name = "mistral-small-latest"
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
            
            if api_key:
                self.client = Mistral(api_key=api_key)
                st.info("🔑 Mistral client initialized")
            else:
                st.error("❌ Mistral API key not found")
                st.info("💡 Please set MISTRAL_API_KEY environment variable or add it to Streamlit secrets")
                
        except Exception as e:
            st.error(f"Error initializing Mistral client: {str(e)}")
    
    def generate_response(self, message: str, context: Optional[str] = None, system_prompt: Optional[str] = None, stream: bool = False):
        """Generate response using Mistral Small with RAG context"""
        if not self.is_available():
            return "Mistral model is not available. Please check API key configuration."
        
        try:
            # Use custom system prompt or default
            active_system_prompt = system_prompt or self.default_system_prompt
            
            # Build user message with context and conversation history
            user_message = message
            
            # Get conversation history for context (last 30 messages)
            conversation_history = ""
            if hasattr(st.session_state, 'messages') and st.session_state.messages:
                recent_messages = st.session_state.messages[-30:]  # Last 30 messages
                history_parts = []
                
                for msg in recent_messages:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if role == 'user':
                        history_parts.append(f"User: {content}")
                    elif role == 'assistant':
                        history_parts.append(f"Assistant: {content}")
                
                if history_parts:
                    conversation_history = "\n".join(history_parts[-20:])  # Keep it manageable
            
            if context and context.strip():
                user_message = f"""**Conversation History:**
{conversation_history}

**Complete Document Content from Uploaded Files:**

{context}

**Instructions:** You have access to the conversation history and COMPLETE content of the user's uploaded documents above. Use this comprehensive information to provide detailed, accurate answers that are contextually aware of the ongoing conversation. Reference specific sections, quote relevant parts, and provide thorough explanations based on both the document content and conversation context.

**Current User Question:** {message}"""
            elif conversation_history:
                user_message = f"""**Conversation History:**
{conversation_history}

**Instructions:** Use the conversation history above to provide contextually aware responses that build on previous exchanges.

**Current User Question:** {message}"""
            
            # Prepare inputs for Mistral API with system prompt
            inputs = [
                {"role": "system", "content": active_system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Define completion arguments
            completion_args = {
                "temperature": 0.7,
                "max_tokens": 10000,
                "top_p": 0.9
            }
            
            # Make the API call using official Mistral SDK
            response = self.client.chat.complete(
                model=self.model_name,
                messages=inputs,
                stream=stream,
                **completion_args
            )
            
            # Extract response content
            if stream:
                return response  # Return the stream object
            else:
                if response and response.choices and len(response.choices) > 0:
                    return response.choices[0].message.content
                else:
                    return "Mistral API error: No response received"
                
        except Exception as e:
            error_str = str(e)
            if "Status 401" in error_str or "Unauthorized" in error_str:
                return "Mistral API error: Invalid API key. Please check your MISTRAL_API_KEY configuration."
            elif "Status 429" in error_str or "rate limit" in error_str.lower():
                return "Mistral API error: Rate limit exceeded. Please wait and try again."
            elif "timeout" in error_str.lower():
                return "Request timed out. Please try again."
            else:
                return f"Mistral API error: {error_str}"
    
    def is_available(self) -> bool:
        """Check if Mistral model is available"""
        return self.client is not None
    
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
        try:
            self.model = MistralModel()
        except Exception as e:
            st.error(f"Error initializing MistralModel: {e}")
            raise
    
    def generate_response(self, message: str, context: Optional[str] = None, stream: bool = False):
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
            system_prompt=self.model.default_system_prompt,
            stream=stream
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