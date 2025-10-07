"""
AI Model Service
Handles AI model integration for chat responses
"""

import os
import httpx
import json
from typing import Optional, Dict, Any, List
from uuid import UUID
from supabase import Client

from app.core.config import settings
from app.services.enhanced_rag import EnhancedRAGService
from app.services.chat import ChatService
from app.models.user import User


class AIService:
    """AI service for generating chat responses"""
    
    def __init__(self, db: Client):
        self.db = db
        self.rag_service = EnhancedRAGService(db)
        self.chat_service = ChatService(db)
        self.mistral_api_key = None
        self.mistral_base_url = "https://api.mistral.ai/v1"
        self._initialize_mistral()
    
    def _initialize_mistral(self):
        """Initialize Mistral HTTP client"""
        try:
            if settings.MISTRAL_API_KEY:
                self.mistral_api_key = settings.MISTRAL_API_KEY
                print("✅ Mistral AI HTTP client initialized")
            else:
                print("⚠️ Mistral API key not configured")
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
            print(f"🤖 Generating response for user {user.id}, conversation {conversation_id}")
            
            if not self.mistral_api_key:
                print("❌ No Mistral API key configured")
                return "AI service is not available. Please check configuration."
            
            # Get conversation context
            context = ""
            if use_rag:
                try:
                    print("📚 Getting RAG context...")
                    context = await self.rag_service.get_conversation_context(
                        message, conversation_id, user.id, max_chunks=20
                    )
                    print(f"✅ RAG context retrieved: {len(context)} chars")
                except Exception as e:
                    print(f"⚠️ RAG context failed: {e}")
                    context = ""
            
            # Get recent conversation history
            try:
                print("💬 Getting recent messages...")
                recent_messages = await self.chat_service.get_recent_messages(
                    conversation_id, user, limit=10
                )
                print(f"✅ Retrieved {len(recent_messages)} recent messages")
            except Exception as e:
                print(f"⚠️ Recent messages failed: {e}")
                recent_messages = []
            
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
            
            # Generate response via HTTP
            model_name = "mistral-small-latest" if mode == "fast" else "mistral-large-latest"
            
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4000,
                "top_p": 0.9
            }
            
            print(f"🚀 Calling Mistral API with model: {model_name}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.mistral_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.mistral_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                )
                
                print(f"📡 Mistral API response: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("choices") and len(result["choices"]) > 0:
                        response_text = result["choices"][0]["message"]["content"]
                        print(f"✅ Generated response: {len(response_text)} chars")
                        return response_text
                    else:
                        print("❌ No choices in Mistral response")
                        return "I apologize, but I couldn't generate a response. Please try again."
                else:
                    error_msg = f"API error: {response.status_code}"
                    error_text = response.text
                    print(f"❌ Mistral API error: {error_msg} - {error_text}")
                    return f"AI service error ({response.status_code}). Please try again."
                
        except Exception as e:
            error_str = str(e)
            print(f"❌ AI Service Error: {error_str}")
            print(f"❌ Error type: {type(e).__name__}")
            
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
            if not self.mistral_api_key:
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
            
            # Generate streaming response via HTTP
            model_name = "mistral-small-latest" if mode == "fast" else "mistral-large-latest"
            
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4000,
                "top_p": 0.9,
                "stream": True
            }
            
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.mistral_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.mistral_api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=30.0
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data)
                                if chunk.get("choices") and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    content = delta.get("content")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
                        
        except Exception as e:
            yield f"Error generating response: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return self.mistral_api_key is not None
    
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