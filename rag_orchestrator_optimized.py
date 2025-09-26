# rag_orchestrator_optimized.py
import os
import gc
import logging
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass
try:
    from vector_retriever import VectorRetriever, Document
except ImportError:
    # Fallback classes
    class Document:
        def __init__(self, content="", metadata=None):
            self.content = content
            self.metadata = metadata or {}
    
    class VectorRetriever:
        def similarity_search(self, query, user_id, k=3, similarity_threshold=0.2):
            return []

try:
    from context_builder import ContextBuilder, ContextConfig
except ImportError:
    # Fallback classes
    class ContextConfig:
        pass
    
    class ContextBuilder:
        def build_context(self, documents, query, user_preferences=None):
            return ""
        
        def get_context_stats(self, context, documents):
            return {"context_length": len(context), "document_count": len(documents)}
try:
    from groq_llm import GroqLLM
except ImportError:
    # Fallback if GroqLLM is not available
    class GroqLLM:
        def __init__(self, *args, **kwargs):
            pass
        
        def generate_response(self, messages, model_type="fast"):
            return "RAG system temporarily unavailable - GroqLLM import failed"
        
        def stream_response(self, messages, model_type="fast"):
            yield "RAG system temporarily unavailable - GroqLLM import failed"
try:
    from error_handler import ErrorHandler, ErrorType, RetryConfig
except ImportError:
    # Fallback error handling classes
    from enum import Enum
    
    class ErrorType(Enum):
        RAG_PIPELINE = "rag_pipeline"
        MODEL_API = "model_api"
    
    class RetryConfig:
        def __init__(self, max_attempts=2, base_delay=1.0):
            self.max_attempts = max_attempts
            self.base_delay = base_delay
    
    class ErrorHandler:
        def handle_error(self, error, error_type, context):
            return type('ErrorInfo', (), {'user_message': str(error)})()
        
        def get_retry_delay(self, attempt, config):
            return config.base_delay * attempt

logger = logging.getLogger(__name__)

@dataclass
class RAGResponse:
    """Response from RAG pipeline"""
    response: str
    context_used: str
    documents_retrieved: List[Document]
    context_stats: Dict[str, Any]
    model_used: str
    success: bool
    error_message: Optional[str] = None

@dataclass
class RAGConfig:
    """Configuration for RAG pipeline with memory optimization"""
    retrieval_k: int = 3  # Reduced from 5 to save memory
    similarity_threshold: float = 0.2  # Increased to be more selective
    context_config: Optional[ContextConfig] = None
    fallback_to_llm_only: bool = True
    max_retries: int = 2

class RAGOrchestrator:
    """Memory-optimized RAG orchestrator with comprehensive error handling and fallbacks"""
    
    def __init__(
        self, 
        vector_retriever: Optional[VectorRetriever] = None,
        context_builder: Optional[ContextBuilder] = None,
        llm: Optional[GroqLLM] = None,
        config: Optional[RAGConfig] = None
    ):
        self.vector_retriever = vector_retriever or VectorRetriever()
        self.context_builder = context_builder or ContextBuilder()
        self.llm = llm or GroqLLM()
        self.config = config or RAGConfig()
        self.error_handler = ErrorHandler()
        self.retry_config = RetryConfig(max_attempts=2, base_delay=1.0)
        
        # Initialize context config if not provided
        if not self.config.context_config:
            self.config.context_config = ContextConfig()
        
        # Track component health
        self.component_health = {
            'vector_retriever': True,
            'context_builder': True,
            'llm': True
        }
    
    def process_query(
        self, 
        query: str, 
        user_id: str,
        model_type: str = "fast",
        user_preferences: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> RAGResponse:
        """
        Process user query with memory-optimized RAG pipeline and comprehensive error handling
        
        Args:
            query: User's question
            user_id: User ID for document filtering
            model_type: "fast" or "premium" model selection
            user_preferences: Optional user preferences for context building
            conversation_history: Optional conversation history for context
            
        Returns:
            RAGResponse with generated answer and metadata
        """
        documents = []
        context = ""
        
        try:
            # Step 1: Retrieve relevant documents with error handling
            documents = self._safe_retrieve_documents(query, user_id)
            
            # Step 2: Build context with error handling
            context = self._safe_build_context(documents, query, user_preferences)
            
            # Step 3: Generate response with fallback logic
            response = self._safe_generate_response(
                query=query,
                context=context,
                model_type=model_type,
                conversation_history=conversation_history
            )
            
            # Step 4: Get context statistics
            context_stats = self._safe_get_context_stats(context, documents)
            
            # Memory cleanup
            self._cleanup_memory()
            
            return RAGResponse(
                response=response,
                context_used=context,
                documents_retrieved=documents,
                context_stats=context_stats,
                model_used=model_type,
                success=True
            )
            
        except Exception as e:
            # Final fallback - basic LLM response
            logger.error(f"RAG pipeline failed completely: {str(e)}")
            error_info = self.error_handler.handle_error(
                e, ErrorType.RAG_PIPELINE, "process_query"
            )
            
            # Memory cleanup on error
            self._cleanup_memory()
            
            # Try one last fallback to basic LLM
            try:
                fallback_response = self._emergency_fallback(query, model_type)
                return RAGResponse(
                    response=fallback_response,
                    context_used="Emergency fallback mode - no document context available",
                    documents_retrieved=[],
                    context_stats={"error": "RAG pipeline failed, using emergency fallback"},
                    model_used=model_type,
                    success=True,
                    error_message=f"RAG pipeline error: {error_info.user_message}"
                )
            except Exception as fallback_error:
                logger.error(f"Emergency fallback also failed: {str(fallback_error)}")
                return RAGResponse(
                    response="I'm experiencing technical difficulties and cannot process your question right now. Please try again in a few moments.",
                    context_used="",
                    documents_retrieved=[],
                    context_stats={},
                    model_used=model_type,
                    success=False,
                    error_message=f"Complete system failure: {str(e)}"
                )
    
    def _safe_retrieve_documents(self, query: str, user_id: str) -> List[Document]:
        """Safely retrieve documents with error handling"""
        try:
            if not self.component_health['vector_retriever']:
                logger.warning("Vector retriever marked as unhealthy, skipping document retrieval")
                return []
            
            documents = self.vector_retriever.similarity_search(
                query=query,
                user_id=user_id,
                k=self.config.retrieval_k,
                similarity_threshold=self.config.similarity_threshold
            )
            
            logger.info(f"Retrieved {len(documents)} documents for query")
            return documents
            
        except Exception as e:
            error_info = self.error_handler.handle_error(
                e, ErrorType.RAG_PIPELINE, "document_retrieval"
            )
            logger.warning(f"Document retrieval failed: {str(e)}")
            self.component_health['vector_retriever'] = False
            return []
    
    def _safe_build_context(
        self, 
        documents: List[Document], 
        query: str, 
        user_preferences: Optional[Dict[str, Any]]
    ) -> str:
        """Safely build context with error handling"""
        try:
            if not self.component_health['context_builder']:
                logger.warning("Context builder marked as unhealthy, using minimal context")
                return ""
            
            if not documents:
                return ""
            
            context = self.context_builder.build_context(
                documents=documents,
                query=query,
                user_preferences=user_preferences
            )
            
            logger.info(f"Built context with {len(context)} characters")
            return context
            
        except Exception as e:
            error_info = self.error_handler.handle_error(
                e, ErrorType.RAG_PIPELINE, "context_building"
            )
            logger.warning(f"Context building failed: {str(e)}")
            self.component_health['context_builder'] = False
            return ""
    
    def _safe_generate_response(
        self,
        query: str,
        context: str,
        model_type: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> str:
        """Safely generate response with multiple fallback attempts"""
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                if context.strip():
                    # Use RAG mode with context
                    response = self._generate_with_context(
                        query=query,
                        context=context,
                        model_type=model_type,
                        conversation_history=conversation_history
                    )
                else:
                    # Fallback to LLM-only mode
                    response = self._generate_without_context(
                        query=query,
                        model_type=model_type,
                        conversation_history=conversation_history
                    )
                
                logger.info(f"Generated response successfully on attempt {attempt}")
                return response
                
            except Exception as e:
                error_info = self.error_handler.handle_error(
                    e, ErrorType.MODEL_API, f"generate_response_attempt_{attempt}"
                )
                
                if attempt == self.retry_config.max_attempts:
                    logger.error(f"Response generation failed after {attempt} attempts")
                    raise e
                
                # Wait before retry
                delay = self.error_handler.get_retry_delay(attempt, self.retry_config)
                logger.info(f"Retrying response generation in {delay:.1f} seconds")
                import time
                time.sleep(delay)
        
        raise Exception("Response generation failed after all attempts")
    
    def _safe_get_context_stats(self, context: str, documents: List[Document]) -> Dict[str, Any]:
        """Safely get context statistics with error handling"""
        try:
            return self.context_builder.get_context_stats(context, documents)
        except Exception as e:
            logger.warning(f"Failed to get context stats: {str(e)}")
            return {
                "context_length": len(context),
                "document_count": len(documents),
                "error": "Failed to calculate detailed stats"
            }
    
    def _emergency_fallback(self, query: str, model_type: str) -> str:
        """Emergency fallback for when everything else fails"""
        try:
            # Minimal system prompt for emergency situations
            messages = [
                {
                    "role": "system", 
                    "content": "You are a helpful pharmacology assistant. Answer the user's question using your general knowledge. Be concise and helpful."
                },
                {"role": "user", "content": query}
            ]
            
            return self.llm.generate_response(messages, model_type)
            
        except Exception as e:
            logger.error(f"Emergency fallback failed: {str(e)}")
            raise e
    
    def stream_query(
        self, 
        query: str, 
        user_id: str,
        model_type: str = "fast",
        user_preferences: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Generator[str, None, RAGResponse]:
        """
        Stream response for user query with memory-optimized RAG pipeline
        """
        try:
            # Step 1: Retrieve relevant documents for the user
            documents = self.vector_retriever.similarity_search(
                query=query,
                user_id=user_id,
                k=self.config.retrieval_k,
                similarity_threshold=self.config.similarity_threshold
            )
            
            # Step 2: Build context from retrieved documents
            context = self.context_builder.build_context(
                documents=documents,
                query=query,
                user_preferences=user_preferences
            )
            
            # Step 3: Stream response using LLM
            response_chunks = []
            
            if context.strip():
                # Use RAG mode with context
                for chunk in self._stream_with_context(
                    query=query,
                    context=context,
                    model_type=model_type,
                    conversation_history=conversation_history
                ):
                    response_chunks.append(chunk)
                    yield chunk
            elif self.config.fallback_to_llm_only:
                # Fallback to LLM-only mode
                context = "No relevant documents found. Using general knowledge."
                for chunk in self._stream_without_context(
                    query=query,
                    model_type=model_type,
                    conversation_history=conversation_history
                ):
                    response_chunks.append(chunk)
                    yield chunk
            else:
                error_msg = "I don't have enough relevant information to answer your question. Please try uploading relevant documents first."
                yield error_msg
                return RAGResponse(
                    response=error_msg,
                    context_used="",
                    documents_retrieved=[],
                    context_stats={},
                    model_used=model_type,
                    success=False,
                    error_message="No relevant documents found and fallback disabled"
                )
            
            # Step 4: Get context statistics
            context_stats = self.context_builder.get_context_stats(context, documents)
            full_response = "".join(response_chunks)
            
            # Memory cleanup
            self._cleanup_memory()
            
            return RAGResponse(
                response=full_response,
                context_used=context,
                documents_retrieved=documents,
                context_stats=context_stats,
                model_used=model_type,
                success=True
            )
            
        except Exception as e:
            error_msg = "I encountered an error while processing your question. Please try again."
            yield error_msg
            # Memory cleanup on error
            self._cleanup_memory()
            return RAGResponse(
                response=error_msg,
                context_used="",
                documents_retrieved=[],
                context_stats={},
                model_used=model_type,
                success=False,
                error_message=str(e)
            )
    
    def _generate_with_context(
        self, 
        query: str, 
        context: str, 
        model_type: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate response using context from retrieved documents"""
        
        # Build the prompt with context
        system_prompt = self._build_system_prompt_with_context(context)
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided (reduced for memory efficiency)
        if conversation_history:
            messages.extend(conversation_history[-2:])  # Keep last 2 messages for context
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Generate response
        return self.llm.generate_response(messages, model_type)
    
    def _generate_without_context(
        self, 
        query: str, 
        model_type: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate response without retrieved context (fallback mode)"""
        
        system_prompt = self._build_system_prompt_without_context()
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided (reduced for memory efficiency)
        if conversation_history:
            messages.extend(conversation_history[-2:])  # Keep last 2 messages for context
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Generate response
        return self.llm.generate_response(messages, model_type)
    
    def _stream_with_context(
        self, 
        query: str, 
        context: str, 
        model_type: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Generator[str, None, None]:
        """Stream response using context from retrieved documents"""
        
        # Build the prompt with context
        system_prompt = self._build_system_prompt_with_context(context)
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided (reduced for memory efficiency)
        if conversation_history:
            messages.extend(conversation_history[-2:])  # Keep last 2 messages for context
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Stream response
        yield from self.llm.stream_response(messages, model_type)
    
    def _stream_without_context(
        self, 
        query: str, 
        model_type: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Generator[str, None, None]:
        """Stream response without retrieved context (fallback mode)"""
        
        system_prompt = self._build_system_prompt_without_context()
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided (reduced for memory efficiency)
        if conversation_history:
            messages.extend(conversation_history[-2:])  # Keep last 2 messages for context
        
        # Add current query
        messages.append({"role": "user", "content": query})
        
        # Stream response
        yield from self.llm.stream_response(messages, model_type)
    
    def _build_system_prompt_with_context(self, context: str) -> str:
        """Build system prompt with retrieved context"""
        return f"""You are a knowledgeable pharmacology assistant. Use the provided context to answer questions accurately and comprehensively.

Context from relevant documents:
{context}

Instructions:
- Answer based primarily on the provided context
- If the context doesn't fully address the question, clearly indicate what information is missing
- Provide specific, actionable information when possible
- Cite relevant sources when appropriate
- If asked about drug interactions, dosages, or medical advice, remind users to consult healthcare professionals
- Be concise but thorough in your explanations"""
    
    def _build_system_prompt_without_context(self) -> str:
        """Build system prompt for fallback mode without context"""
        return """You are a knowledgeable pharmacology assistant. Provide accurate, helpful information about pharmacology topics.

Instructions:
- Use your general knowledge to answer questions
- Be clear about the limitations of your knowledge
- For specific drug information, dosages, or medical advice, always recommend consulting healthcare professionals
- Provide educational information while emphasizing the importance of professional medical guidance
- Be concise but thorough in your explanations"""
    
    def _cleanup_memory(self):
        """Force garbage collection to free up memory"""
        gc.collect()