# context_builder.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from vector_retriever import Document

@dataclass
class ContextConfig:
    """Configuration for context building with memory optimization"""
    max_context_length: int = 2000  # Reduced from 4000 to save memory
    max_documents: int = 3  # Reduced from 5 to save memory
    similarity_threshold: float = 0.1
    prioritize_recent: bool = True
    include_source_info: bool = True

class ContextBuilder:
    """Build context for RAG pipeline with user document prioritization"""
    
    def __init__(self, config: Optional[ContextConfig] = None):
        self.config = config or ContextConfig()
    
    def build_context(
        self, 
        documents: List[Document], 
        query: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build context string from retrieved documents with intelligent prioritization
        
        Args:
            documents: List of retrieved documents
            query: Original user query
            user_preferences: Optional user preferences for context building
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        # Apply user preferences if provided
        effective_config = self._apply_user_preferences(user_preferences)
        
        # Filter documents by similarity threshold
        filtered_docs = [
            doc for doc in documents 
            if doc.similarity and doc.similarity >= effective_config.similarity_threshold
        ]
        
        # Prioritize documents
        prioritized_docs = self._prioritize_documents(filtered_docs, query, effective_config)
        
        # Limit number of documents
        selected_docs = prioritized_docs[:effective_config.max_documents]
        
        # Build context string with length constraints
        context = self._format_context(selected_docs, effective_config)
        
        return context
    
    def _apply_user_preferences(self, user_preferences: Optional[Dict[str, Any]]) -> ContextConfig:
        """Apply user preferences to context configuration"""
        if not user_preferences:
            return self.config
        
        config = ContextConfig(
            max_context_length=user_preferences.get('max_context_length', self.config.max_context_length),
            max_documents=user_preferences.get('max_documents', self.config.max_documents),
            similarity_threshold=user_preferences.get('similarity_threshold', self.config.similarity_threshold),
            prioritize_recent=user_preferences.get('prioritize_recent', self.config.prioritize_recent),
            include_source_info=user_preferences.get('include_source_info', self.config.include_source_info)
        )
        
        return config
    
    def _prioritize_documents(
        self, 
        documents: List[Document], 
        query: str, 
        config: ContextConfig
    ) -> List[Document]:
        """
        Prioritize documents based on similarity, recency, and relevance
        
        Args:
            documents: List of documents to prioritize
            query: Original query for relevance scoring
            config: Context configuration
            
        Returns:
            Prioritized list of documents
        """
        if not documents:
            return []
        
        # Calculate priority scores
        scored_docs = []
        for doc in documents:
            score = self._calculate_priority_score(doc, query, config)
            scored_docs.append((doc, score))
        
        # Sort by priority score (descending)
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, _ in scored_docs]
    
    def _calculate_priority_score(
        self, 
        document: Document, 
        query: str, 
        config: ContextConfig
    ) -> float:
        """
        Calculate priority score for a document
        
        Args:
            document: Document to score
            query: Original query
            config: Context configuration
            
        Returns:
            Priority score (higher is better)
        """
        score = 0.0
        
        # Base similarity score (most important factor)
        if document.similarity:
            score += document.similarity * 10.0
        
        # Boost for exact keyword matches
        query_lower = query.lower()
        content_lower = document.content.lower()
        
        # Count keyword matches
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        keyword_matches = len(query_words.intersection(content_words))
        score += keyword_matches * 0.5
        
        # Boost for document length (prefer substantial content)
        content_length = len(document.content)
        if 200 <= content_length <= 2000:  # Sweet spot for chunk size
            score += 1.0
        elif content_length > 2000:
            score += 0.5
        
        # Boost for certain file types (if metadata available)
        if document.metadata:
            file_type = document.metadata.get('file_type', '')
            if file_type in ['pdf', 'docx']:  # Prefer structured documents
                score += 0.5
        
        # Recency boost (if enabled and metadata available)
        if config.prioritize_recent and document.metadata:
            # This would require timestamp information in metadata
            # For now, we'll use chunk_index as a proxy (lower index = earlier in document)
            chunk_index = document.metadata.get('chunk_index', 0)
            if chunk_index == 0:  # First chunk often contains important info
                score += 0.3
        
        return score
    
    def _format_context(self, documents: List[Document], config: ContextConfig) -> str:
        """
        Format documents into context string with strict length constraints for memory efficiency
        
        Args:
            documents: List of documents to format
            config: Context configuration
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        current_length = 0
        max_doc_length = 500  # Limit individual document length
        
        for i, doc in enumerate(documents):
            # Truncate document content if too long
            content = doc.content
            if len(content) > max_doc_length:
                content = content[:max_doc_length] + "..."
            
            # Format document section
            if config.include_source_info:
                source_info = f"Source: {doc.source}"
                if doc.similarity:
                    source_info += f" (Relevance: {doc.similarity:.2f})"
                
                doc_section = f"Document {i+1} - {source_info}:\n{content}\n"
            else:
                doc_section = f"{content}\n"
            
            # Check if adding this document would exceed length limit
            if current_length + len(doc_section) > config.max_context_length:
                break
            
            context_parts.append(doc_section)
            current_length += len(doc_section)
        
        result = "\n".join(context_parts).strip()
        
        # Final safety check - truncate if still too long
        if len(result) > config.max_context_length:
            result = result[:config.max_context_length - 3] + "..."
        
        return result
    
    def get_context_stats(self, context: str, documents: List[Document]) -> Dict[str, Any]:
        """
        Get statistics about the built context
        
        Args:
            context: Built context string
            documents: Original documents used
            
        Returns:
            Dictionary with context statistics
        """
        return {
            'context_length': len(context),
            'document_count': len(documents),
            'avg_similarity': sum(doc.similarity or 0 for doc in documents) / len(documents) if documents else 0,
            'sources': list(set(doc.source for doc in documents)),
            'total_original_length': sum(len(doc.content) for doc in documents)
        }