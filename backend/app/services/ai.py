"""
AI Model Service
Handles AI model integration for chat responses
"""

import os
import httpx
import json
import asyncio
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
            return """You are PharmGPT, an expert pharmacology assistant. Provide clear, accurate, and concise responses about pharmaceutical topics, drug interactions, mechanisms of action, and clinical applications. Keep responses focused and to the point.

IMPORTANT: When document context is provided, you MUST base your answer primarily on that context. Reference specific information from the documents."""
        else:
            return """You are PharmGPT, an expert pharmacology assistant. Provide detailed, comprehensive, and scientifically accurate responses about pharmaceutical topics, drug interactions, mechanisms of action, and clinical applications. Always provide elaborate and detailed explanations unless specifically asked for brevity.

CRITICAL INSTRUCTIONS FOR DOCUMENT CONTEXT:
1. When document context is provided, you MUST prioritize information from those documents
2. Base your answer primarily on the document content
3. Quote or reference specific sections from the documents when relevant
4. If the documents contain the answer, use that information first before adding general knowledge
5. If the question cannot be answered from the documents, clearly state that and then provide general knowledge
6. Always acknowledge when you're using information from the uploaded documents"""
    
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
            
            # Get conversation context using semantic search
            context = ""
            context_used = False
            if use_rag:
                try:
                    print("📚 Getting RAG context with semantic search...")
                    # Use semantic search to find relevant chunks
                    context = await self.rag_service.get_conversation_context(
                        message, conversation_id, user.id, max_chunks=20
                    )
                    
                    if context:
                        context_used = True
                        print(f"✅ RAG context retrieved: {len(context)} chars")
                        print(f"📄 Context preview: {context[:200]}...")
                    else:
                        print("⚠️ No relevant context found, trying all chunks...")
                        # Fallback: get all chunks if semantic search returns nothing
                        all_chunks = await self.rag_service.get_all_conversation_chunks(
                            conversation_id, user.id
                        )
                        if all_chunks:
                            context_parts = []
                            for chunk in all_chunks[:20]:  # Limit to first 20 chunks
                                context_parts.append(chunk.content)
                            context = "\n\n".join(context_parts)
                            context_used = True
                            print(f"✅ Fallback context: {len(all_chunks)} chunks, {len(context)} chars")
                            print(f"📄 Context preview: {context[:200]}...")
                except Exception as e:
                    print(f"⚠️ RAG context failed: {e}")
                    import traceback
                    traceback.print_exc()
                    context = ""
                    context_used = False
            
            # Get recent conversation history
            try:
                print("💬 Getting recent messages...")
                # Limit history for detailed mode
                history_limit = 6 if mode == "detailed" else 8
                recent_messages = await self.chat_service.get_recent_messages(
                    conversation_id, user, limit=history_limit
                )
                print(f"✅ Retrieved {len(recent_messages)} recent messages")
            except Exception as e:
                print(f"⚠️ Recent messages failed: {e}")
                recent_messages = []
            
            # Build conversation history
            conversation_history = []
            for msg in recent_messages:
                # Truncate long messages to save tokens
                content = msg.content[:500] if len(msg.content) > 500 else msg.content
                conversation_history.append({
                    "role": msg.role,
                    "content": content
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
            
            # Set max_tokens to 8000 for comprehensive responses
            max_tokens = 8000
            
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": max_tokens,
                "top_p": 0.9
            }
            
            print(f"🚀 Calling Mistral API with model: {model_name}, max_tokens: {max_tokens}")
            
            # Retry logic for rate limits (429 errors)
            max_retries = 3
            retry_delays = [2, 5, 10]  # Exponential backoff: 2s, 5s, 10s
            
            for attempt in range(max_retries):
                try:
                    # 3 minute timeout for processing
                    async with httpx.AsyncClient(timeout=180.0) as client:
                        response = await client.post(
                            f"{self.mistral_base_url}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {self.mistral_api_key}",
                                "Content-Type": "application/json"
                            },
                            json=payload
                        )
                        
                        print(f"📡 Mistral API response: {response.status_code}")
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("choices") and len(result["choices"]) > 0:
                                response_text = result["choices"][0]["message"]["content"]
                                print(f"✅ Generated response: {len(response_text)} chars")
                                
                                # Log if context was used (for debugging only)
                                if context_used and context:
                                    print(f"📚 Response generated using document context")
                                
                                return response_text
                            else:
                                print("❌ No choices in Mistral response")
                                return "I apologize, but I couldn't generate a response. Please try again."
                        
                        elif response.status_code == 429:
                            # Rate limit error - retry with backoff
                            if attempt < max_retries - 1:
                                delay = retry_delays[attempt]
                                print(f"⏳ Rate limit hit (429), retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
                                await asyncio.sleep(delay)
                                continue
                            else:
                                print(f"❌ Rate limit exceeded after {max_retries} attempts")
                                return "The AI service is currently experiencing high demand. Please try again in a moment."
                        
                        else:
                            error_msg = f"API error: {response.status_code}"
                            error_text = response.text
                            print(f"❌ Mistral API error: {error_msg} - {error_text}")
                            return f"AI service error ({response.status_code}). Please try again."
                
                except httpx.TimeoutException:
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        print(f"⏳ Request timeout, retrying in {delay}s (attempt {attempt + 1}/{max_retries})...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print(f"❌ Request timed out after {max_retries} attempts")
                        return "Request timed out. Please try again."
                
                except Exception as request_error:
                    print(f"❌ Request error: {request_error}")
                    raise  # Re-raise to be caught by outer exception handler
                
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
        
        # Add conversation history if available (already truncated in caller)
        if conversation_history:
            parts.append("**Previous Conversation:**")
            for msg in conversation_history:
                role = "You" if msg["role"] == "assistant" else "User"
                parts.append(f"{role}: {msg['content']}")
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