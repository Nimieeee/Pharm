# rag_orchestrator.py
import os
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass
from vector_retriever import VectorRetriever, Document
from context_builder import ContextBuilder, ContextConfig
from groq_llm import GroqLLM

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
    """Enhanced RAG orchestrator with user-specific context retrieval"""
    
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
        
        # Initialize context config if not provided
        if not self.config.context_config:
            self.config.context_config = ContextConfig()
    
    def process_query(
        self, 
        query: str, 
        user_id: str,
        model_type: str = "fast",
        user_preferences: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> RAGResponse:
        """
        Process user query with RAG pipeline
        
        Args:
            query: User's question
            user_id: User ID for document filtering
            model_type: "fast" or "premium" model selection
            user_preferences: Optional user preferences for context building
            conversation_history: Optional conversation history for context
            
        Returns:
            RAGResponse with generated answer and metadata
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
            
            # Step 3: Generate response using LLM
            if context.strip():
                # Use RAG mode with context
                response = self._generate_with_context(
                    query=query,
                    context=context,
                    model_type=model_type,
                    conversation_history=conversation_history
                )
            elif self.config.fallback_to_llm_only:
                # Fallback to LLM-only mode
                response = self._generate_without_context(
                    query=query,
                    model_type=model_type,
                    conversation_history=conversation_history
                )
                context = "No relevant documents found. Using general knowledge."
            else:
                return RAGResponse(
                    response="I don't have enough relevant information to answer your question. Please try uploading relevant documents first.",
                    context_used="",
                    documents_retrieved=[],
                    context_stats={},
                    model_used=model_type,
                    success=False,
                    error_message="No relevant documents found and fallback disabled"
                )
            
            # Step 4: Get context statistics
            context_stats = self.context_builder.get_context_stats(context, documents)
            
            return RAGResponse(
                response=response,
                context_used=context,
                documents_retrieved=documents,
                context_stats=context_stats,
                model_used=model_type,
                success=True
            )
            
        except Exception as e:
            return RAGResponse(
                response="I encountered an error while processing your question. Please try again.",
                context_used="",
                documents_retrieved=[],
                context_stats={},
                model_used=model_type,
                success=False,
                error_message=str(e)
            )
    
    def stream_query(
        self, 
        query: str, 
        user_id: str,
        model_type: str = "fast",
        user_preferences: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Generator[str, None, RAGResponse]:
        """
        Stream response for user query with RAG pipeline
        
        Args:
            query: User's question
            user_id: User ID for document filtering
            model_type: "fast" or "premium" model selection
            user_preferences: Optional user preferences for context building
            conversation_history: Optional conversation history for context
            
        Yields:
            Response chunks as they are generated
            
        Returns:
            Final RAGResponse with metadata
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
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Keep last 6 messages for context
        
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
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Keep last 6 messages for context
        
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
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Keep last 6 messages for context
        
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
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history[-6:])  # Keep last 6 messages for context
        
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