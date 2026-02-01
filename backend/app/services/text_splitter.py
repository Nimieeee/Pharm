"""
Enhanced Text Splitter using LangChain RecursiveCharacterTextSplitter
Handles intelligent text chunking with metadata preservation
"""

import logging
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedTextSplitter:
    """Enhanced text splitter using LangChain RecursiveCharacterTextSplitter"""
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize the text splitter with configurable parameters
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to use for splitting
        """
        self.chunk_size = chunk_size or settings.LANGCHAIN_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.LANGCHAIN_CHUNK_OVERLAP
        
        # Default separators optimized for various document types
        self.separators = separators or [
            "\n\n",  # Paragraph breaks
            "\n",    # Line breaks
            ". ",    # Sentence endings
            "! ",    # Exclamation sentences
            "? ",    # Question sentences
            "; ",    # Semicolon breaks
            ", ",    # Comma breaks
            " ",     # Word breaks
            ""       # Character breaks (last resort)
        ]
        
        # Initialize the LangChain splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False,
            keep_separator=True
        )
        
        logger.info(
            f"✅ Enhanced text splitter initialized "
            f"(chunk_size={self.chunk_size}, overlap={self.chunk_overlap})"
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks while preserving metadata
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            List of chunked Document objects with enhanced metadata
        """
        if not documents:
            logger.warning("⚠️  No documents provided for splitting")
            return []
        
        all_chunks = []
        total_input_chars = 0
        
        for doc_index, document in enumerate(documents):
            try:
                # Track input statistics
                input_length = len(document.page_content)
                total_input_chars += input_length
                
                if input_length == 0:
                    logger.warning(f"⚠️  Skipping empty document at index {doc_index}")
                    continue
                
                # Handle very small documents
                if input_length <= self.chunk_size:
                    # Document is small enough, keep as single chunk
                    enhanced_doc = Document(
                        page_content=document.page_content,
                        metadata=self._enhance_metadata(
                            document.metadata.copy(),
                            chunk_index=0,
                            total_chunks=1,
                            doc_index=doc_index,
                            chunk_size=input_length,
                            is_complete_document=True
                        )
                    )
                    all_chunks.append(enhanced_doc)
                    continue
                
                # Split the document
                chunks = self.splitter.split_documents([document])
                
                if not chunks:
                    logger.warning(f"⚠️  No chunks generated for document at index {doc_index}")
                    continue
                
                # Enhance metadata for each chunk
                for chunk_index, chunk in enumerate(chunks):
                    chunk.metadata = self._enhance_metadata(
                        chunk.metadata.copy(),
                        chunk_index=chunk_index,
                        total_chunks=len(chunks),
                        doc_index=doc_index,
                        chunk_size=len(chunk.page_content),
                        is_complete_document=False
                    )
                    all_chunks.append(chunk)
                
                logger.debug(
                    f"Split document {doc_index} ({input_length} chars) into {len(chunks)} chunks"
                )
                
            except Exception as e:
                logger.error(f"❌ Error splitting document at index {doc_index}: {e}")
                # Create a fallback chunk with error information
                fallback_chunk = Document(
                    page_content=document.page_content[:self.chunk_size] if document.page_content else "",
                    metadata=self._enhance_metadata(
                        document.metadata.copy(),
                        chunk_index=0,
                        total_chunks=1,
                        doc_index=doc_index,
                        chunk_size=min(len(document.page_content), self.chunk_size),
                        is_complete_document=False,
                        processing_error=str(e)
                    )
                )
                all_chunks.append(fallback_chunk)
        
        # Log splitting statistics
        total_output_chars = sum(len(chunk.page_content) for chunk in all_chunks)
        logger.info(
            f"✅ Text splitting completed: {len(documents)} documents → {len(all_chunks)} chunks "
            f"({total_input_chars} → {total_output_chars} chars)"
        )
        
        return all_chunks
    
    def _enhance_metadata(
        self,
        metadata: Dict[str, Any],
        chunk_index: int,
        total_chunks: int,
        doc_index: int,
        chunk_size: int,
        is_complete_document: bool,
        processing_error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhance chunk metadata with splitting information"""
        
        # Add chunking metadata
        metadata.update({
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "document_index": doc_index,
            "chunk_size": chunk_size,
            "is_complete_document": is_complete_document,
            "splitter_config": {
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "splitter_type": "RecursiveCharacterTextSplitter"
            }
        })
        
        # Add error information if present
        if processing_error:
            metadata["processing_error"] = processing_error
            metadata["processing_status"] = "error"
        else:
            metadata["processing_status"] = "success"
        
        # Add chunk position information
        if total_chunks > 1:
            if chunk_index == 0:
                metadata["chunk_position"] = "first"
            elif chunk_index == total_chunks - 1:
                metadata["chunk_position"] = "last"
            else:
                metadata["chunk_position"] = "middle"
        else:
            metadata["chunk_position"] = "single"
        
        return metadata
    
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Split raw text into chunks
        
        Args:
            text: Raw text to split
            metadata: Optional metadata to add to all chunks
            
        Returns:
            List of Document objects
        """
        if not text or not text.strip():
            logger.warning("⚠️  Empty text provided for splitting")
            return []
        
        # Create a temporary document
        document = Document(
            page_content=text.strip(),
            metadata=metadata or {}
        )
        
        return self.split_documents([document])
    
    def get_optimal_chunk_size(self, text: str, target_chunks: int = 5) -> int:
        """
        Calculate optimal chunk size for a given text to achieve target number of chunks
        
        Args:
            text: Input text
            target_chunks: Desired number of chunks
            
        Returns:
            Recommended chunk size
        """
        if not text:
            return self.chunk_size
        
        text_length = len(text)
        
        if text_length <= self.chunk_size:
            return text_length
        
        # Calculate optimal size considering overlap
        effective_chunk_size = (text_length + (target_chunks - 1) * self.chunk_overlap) / target_chunks
        
        # Round to reasonable boundaries
        optimal_size = max(200, min(int(effective_chunk_size), 5000))
        
        logger.debug(
            f"Optimal chunk size for {text_length} chars targeting {target_chunks} chunks: {optimal_size}"
        )
        
        return optimal_size
    
    def analyze_splitting_efficiency(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Analyze how efficiently documents would be split
        
        Args:
            documents: Documents to analyze
            
        Returns:
            Analysis results
        """
        if not documents:
            return {"error": "No documents provided"}
        
        analysis = {
            "total_documents": len(documents),
            "total_input_chars": 0,
            "estimated_chunks": 0,
            "documents_needing_split": 0,
            "small_documents": 0,
            "large_documents": 0,
            "average_document_size": 0,
            "size_distribution": {
                "tiny": 0,      # < 100 chars
                "small": 0,     # 100-500 chars
                "medium": 0,    # 500-1500 chars
                "large": 0,     # 1500-3000 chars
                "very_large": 0 # > 3000 chars
            }
        }
        
        document_sizes = []
        
        for doc in documents:
            size = len(doc.page_content)
            document_sizes.append(size)
            analysis["total_input_chars"] += size
            
            # Estimate chunks for this document
            if size <= self.chunk_size:
                analysis["estimated_chunks"] += 1
                analysis["small_documents"] += 1
            else:
                # Rough estimation of chunks
                estimated = max(1, (size - self.chunk_overlap) // (self.chunk_size - self.chunk_overlap))
                analysis["estimated_chunks"] += estimated
                analysis["documents_needing_split"] += 1
                
                if size > 3000:
                    analysis["large_documents"] += 1
            
            # Size distribution
            if size < 100:
                analysis["size_distribution"]["tiny"] += 1
            elif size < 500:
                analysis["size_distribution"]["small"] += 1
            elif size < 1500:
                analysis["size_distribution"]["medium"] += 1
            elif size < 3000:
                analysis["size_distribution"]["large"] += 1
            else:
                analysis["size_distribution"]["very_large"] += 1
        
        if document_sizes:
            analysis["average_document_size"] = analysis["total_input_chars"] / len(documents)
            analysis["min_document_size"] = min(document_sizes)
            analysis["max_document_size"] = max(document_sizes)
        
        # Add recommendations
        analysis["recommendations"] = []
        
        if analysis["size_distribution"]["very_large"] > len(documents) * 0.3:
            analysis["recommendations"].append("Consider increasing chunk_size for better efficiency")
        
        if analysis["size_distribution"]["tiny"] > len(documents) * 0.3:
            analysis["recommendations"].append("Many documents are very small - consider combining them")
        
        if analysis["estimated_chunks"] > len(documents) * 10:
            analysis["recommendations"].append("High chunk count expected - consider larger chunk_size")
        
        return analysis
    
    def get_splitter_config(self) -> Dict[str, Any]:
        """Get current splitter configuration"""
        return {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "separators": self.separators,
            "splitter_type": "RecursiveCharacterTextSplitter",
            "langchain_version": "0.1.0"
        }
    
    def update_config(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None
    ) -> None:
        """Update splitter configuration"""
        if chunk_size is not None:
            self.chunk_size = chunk_size
        
        if chunk_overlap is not None:
            self.chunk_overlap = chunk_overlap
        
        if separators is not None:
            self.separators = separators
        
        # Recreate the splitter with new config
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False,
            keep_separator=True
        )
        
        logger.info(f"✅ Text splitter configuration updated")


# Global text splitter instance
text_splitter = EnhancedTextSplitter()