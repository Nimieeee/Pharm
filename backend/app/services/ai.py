"""
AI Model Service
Handles AI model integration for chat responses
"""

import os
from typing import Optional, Dict, Any, List
from uuid import UUID
from supabase import Client

from app.core.config import settings
from app.services.enhanced_rag import EnhancedRAGService
from app.services.chat import ChatService
from app.models.user import User

# Import Mistral AI
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    print("❌ Mistral AI not available. Install with: pip install mistralai")


class AIService:
    """AI service for generating chat responses"""
    
    def __init__(self, db: Client):
        self.db = db
        self.rag_service = EnhancedRAGService(db)
        self.chat_service = ChatService(db)
        self.mistral_client = None
        self._initialize_mistral()
    
    def _initialize_mistral(self):
        """Initialize Mistral client"""
        try:
            if MISTRAL_AVAILABLE and settings.MISTRAL_API_KEY:
                self.mistral_client = Mistral(api_key=settings.MISTRAL_API_KEY)
                print("✅ Mistral AI client initialized")
            else:
                print("⚠️ Mistral AI not configured")
        except Exception as e:
            print(f"❌ Error initializing Mistral: {e}")
    
    def _get_system_prompt(self, mode: str = "detailed") -> str:
        """Get system prompt based on mode"""
        if mode == "fast":
            return """You are PharmGPT, an expert pharmacology assistant. Provide clear, accurate, and concise responses about pharmaceutical topics, drug interactions, mechanisms of action, and clinical applications. Keep responses focused and to the point."""
        else:
            return """You are PharmGPT, an expert pharmacology assistant. Provide detailed, comprehensive, and scientifically accurate responses about pharmaceutical topics, drug interactions, mechanisms of action, and clinical applications. Always provide elaborate and detailed explanations unless specifically asked for brevity.

When provided with document context, use it to give more accurate and specific answers. Reference the documents when relevant and provide detailed explanations based on the available information."""
    
    async def generate_response(
        self,
        message: str,
        conversation_id: UUID,
        user: User,
        mode: str = "detailed",
        use_rag: bool = True
    ) -> str:
        """Generate AI response for a message"""
        try:
            if not self.mistral_client:
                return "AI service is not available. Please check configuration."
            
            # Get conversation context
            context = ""
            if use_rag:
                context = await self.rag_service.get_conversation_context(
                    message, conversation_id, user.id, max_chunks=20
                )
            
            # Get recent conversation history
            recent_messages = await self.chat_service.get_recent_messages(
                conversation_id, user, limit=10
            )
            
            # Build conversation history
            conversation_history = []
            for msg in recent_messages[-10:]:  # Last 10 messages
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Build user message with context
            user_message = self._build_user_message(message, context, conversation_history)
            
            # Prepare messages for Mistral
            messages = [
                {"role": "system", "content": self._get_system_prompt(mode)},
                {"role": "user", "content": user_message}
            ]
            
            # Generate response
            model_name = "mistral-small-latest" if mode == "fast" else "mistral-large-latest"
            
            response = self.mistral_client.chat.complete(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=4000,
                top_p=0.9
            )
            
            if response and response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                return "I apologize, but I couldn't generate a response. Please try again."
                
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "Unauthorized" in error_str:
                return "AI service authentication error. Please check API configuration."
            elif "429" in error_str or "rate limit" in error_str.lower():
                return "AI service is temporarily busy. Please try again in a moment."
            elif "timeout" in error_str.lower():
                return "Request timed out. Please try again."
            else:
                return f"I encountered an error while processing your request: {error_str}"
    
    def _build_user_message(
        self, 
        message: str, 
        context: str, 
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """Build user message with context and history"""
        parts = []
        
        # Add conversation history if available
        if conversation_history:
            parts.append("**Previous Conversation:**")
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                role = "You" if msg["role"] == "assistant" else "User"
                parts.append(f"{role}: {msg['content'][:200]}...")  # Truncate for brevity
            parts.append("")
        
        # Add document context if available
        if context and context.strip():
            parts.append("**Document Context:**")
            parts.append(context)
            parts.append("")
            parts.append("**Instructions:** Use the document context above to provide accurate, detailed answers. Reference specific information from the documents when relevant.")
            parts.append("")
        
        # Add current user question
        parts.append(f"**Current Question:** {message}")
        
        return "\n".join(parts)
    
    async def generate_streaming_response(
        self,
        message: str,
        conversation_id: UUID,
        user: User,
        mode: str = "detailed",
        use_rag: bool = True
    ):
        """Generate streaming AI response"""
        try:
            if not self.mistral_client:
                yield "AI service is not available. Please check configuration."
                return
            
            # Get context (same as non-streaming)
            context = ""
            if use_rag:
                context = await self.rag_service.get_conversation_context(
                    message, conversation_id, user.id, max_chunks=20
                )
            
            # Get recent conversation history
            recent_messages = await self.chat_service.get_recent_messages(
                conversation_id, user, limit=10
            )
            
            conversation_history = []
            for msg in recent_messages[-10:]:
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Build user message
            user_message = self._build_user_message(message, context, conversation_history)
            
            # Prepare messages
            messages = [
                {"role": "system", "content": self._get_system_prompt(mode)},
                {"role": "user", "content": user_message}
            ]
            
            # Generate streaming response
            model_name = "mistral-small-latest" if mode == "fast" else "mistral-large-latest"
            
            stream = self.mistral_client.chat.complete(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=4000,
                top_p=0.9,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield delta.content
                        
        except Exception as e:
            yield f"Error generating response: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.mistral_client is not None
    
    def get_available_modes(self) -> Dict[str, str]:
        """Get available AI modes"""
        return {
            "fast": "Fast responses using Mistral Small",
            "detailed": "Detailed responses using Mistral Large"
        }
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get AI model information"""
        return {
            "provider": "Mistral AI",
            "available": self.is_available(),
            "modes": self.get_available_modes(),
            "features": [
                "RAG Integration",
                "Conversation Context",
                "Streaming Responses",
                "Pharmacology Expertise"
            ]
        }