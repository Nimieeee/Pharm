"""
Enhanced Document Loaders using LangChain
Handles document loading and processing with comprehensive error handling
"""

import os
import tempfile
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Custom exception for document processing errors"""
    pass


class EnhancedDocumentLoader:
    """Enhanced document loader using LangChain with comprehensive error handling"""
    
    def __init__(self):
        self.supported_extensions = {
            '.pdf': self._load_pdf,
            '.txt': self._load_text,
            '.md': self._load_text,
            '.docx': self._load_docx,
        }
        logger.info("✅ Enhanced document loader initialized")
    
    def is_supported_format(self, filename: str) -> bool:
        """Check if file format is supported"""
        file_extension = Path(filename).suffix.lower()
        return file_extension in self.supported_extensions
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return list(self.supported_extensions.keys())
    
    async def load_document(
        self, 
        file_content: bytes, 
        filename: str, 
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Load document from file content using appropriate LangChain loader
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            additional_metadata: Additional metadata to add to documents
            
        Returns:
            List of LangChain Document objects
            
        Raises:
            DocumentProcessingError: If document processing fails
        """
        if not file_content:
            raise DocumentProcessingError("Empty file content provided")
        
        file_extension = Path(filename).suffix.lower()
        
        if not self.is_supported_format(filename):
            raise DocumentProcessingError(
                f"Unsupported file format: {file_extension}. "
                f"Supported formats: {', '.join(self.get_supported_formats())}"
            )
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name
        
        try:
            # Load document using appropriate loader
            loader_func = self.supported_extensions[file_extension]
            documents = await loader_func(tmp_file_path, filename)
            
            if not documents:
                raise DocumentProcessingError(f"No content extracted from file: {filename}")
            
            # Add additional metadata
            if additional_metadata:
                for doc in documents:
                    doc.metadata.update(additional_metadata)
            
            # Add common metadata
            for doc in documents:
                doc.metadata.update({
                    "filename": filename,
                    "file_type": file_extension.lstrip('.'),
                    "loader_version": "langchain",
                    "total_pages": len(documents) if file_extension == '.pdf' else 1
                })
            
            logger.info(f"✅ Successfully loaded {len(documents)} document(s) from {filename}")
            return documents
            
        except DocumentProcessingError:
            raise
        except Exception as e:
            logger.error(f"❌ Error loading document {filename}: {e}")
            raise DocumentProcessingError(f"Failed to process {filename}: {str(e)}")
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                logger.warning(f"⚠️  Failed to clean up temporary file: {e}")
    
    async def _load_pdf(self, file_path: str, filename: str) -> List[Document]:
        """Load PDF document using PyPDFLoader"""
        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            
            if not documents:
                raise DocumentProcessingError("No content extracted from PDF")
            
            # Add page numbers and enhance metadata
            for i, doc in enumerate(documents):
                doc.metadata.update({
                    "page": i + 1,
                    "source": filename,
                    "loader": "PyPDFLoader"
                })
                
                # Clean up extracted text
                if doc.page_content:
                    doc.page_content = self._clean_text(doc.page_content)
            
            # Filter out empty pages
            documents = [doc for doc in documents if doc.page_content.strip()]
            
            if not documents:
                raise DocumentProcessingError("PDF contains no readable text content")
            
            logger.debug(f"Extracted {len(documents)} pages from PDF: {filename}")
            return documents
            
        except Exception as e:
            if "PDF" in str(e) or "corrupt" in str(e).lower():
                raise DocumentProcessingError(f"Corrupted or invalid PDF file: {filename}")
            raise DocumentProcessingError(f"PDF processing error: {str(e)}")
    
    async def _load_text(self, file_path: str, filename: str) -> List[Document]:
        """Load text document using TextLoader with encoding detection"""
        encodings_to_try = ['utf-8', 'utf-16', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                loader = TextLoader(file_path, encoding=encoding)
                documents = loader.load()
                
                if documents and documents[0].page_content.strip():
                    # Clean and enhance the document
                    doc = documents[0]
                    doc.page_content = self._clean_text(doc.page_content)
                    doc.metadata.update({
                        "source": filename,
                        "encoding": encoding,
                        "loader": "TextLoader"
                    })
                    
                    logger.debug(f"Successfully loaded text file {filename} with encoding {encoding}")
                    return [doc]
                    
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"⚠️  Error with encoding {encoding} for {filename}: {e}")
                continue
        
        raise DocumentProcessingError(
            f"Could not decode text file {filename} with any supported encoding: "
            f"{', '.join(encodings_to_try)}"
        )
    
    async def _load_docx(self, file_path: str, filename: str) -> List[Document]:
        """Load DOCX document using Docx2txtLoader"""
        try:
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
            
            if not documents or not documents[0].page_content.strip():
                raise DocumentProcessingError("No content extracted from DOCX file")
            
            # Clean and enhance the document
            doc = documents[0]
            doc.page_content = self._clean_text(doc.page_content)
            doc.metadata.update({
                "source": filename,
                "loader": "Docx2txtLoader"
            })
            
            logger.debug(f"Successfully loaded DOCX file: {filename}")
            return [doc]
            
        except Exception as e:
            if "docx" in str(e).lower() or "corrupt" in str(e).lower():
                raise DocumentProcessingError(f"Corrupted or invalid DOCX file: {filename}")
            raise DocumentProcessingError(f"DOCX processing error: {str(e)}")
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        import re
        
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    async def validate_document_content(self, documents: List[Document]) -> Dict[str, Any]:
        """Validate loaded document content and return statistics"""
        if not documents:
            return {
                "valid": False,
                "error": "No documents provided",
                "stats": {}
            }
        
        stats = {
            "document_count": len(documents),
            "total_characters": 0,
            "total_words": 0,
            "average_page_length": 0,
            "empty_pages": 0,
            "pages_with_content": 0
        }
        
        for doc in documents:
            content = doc.page_content.strip()
            if content:
                stats["pages_with_content"] += 1
                stats["total_characters"] += len(content)
                stats["total_words"] += len(content.split())
            else:
                stats["empty_pages"] += 1
        
        if stats["pages_with_content"] > 0:
            stats["average_page_length"] = stats["total_characters"] / stats["pages_with_content"]
        
        # Validation rules
        validation_result = {
            "valid": True,
            "warnings": [],
            "stats": stats
        }
        
        if stats["pages_with_content"] == 0:
            validation_result["valid"] = False
            validation_result["error"] = "No pages contain readable content"
        elif stats["total_characters"] < 50:
            validation_result["warnings"].append("Document contains very little text content")
        elif stats["empty_pages"] > stats["pages_with_content"]:
            validation_result["warnings"].append("More than half of the pages are empty")
        
        return validation_result
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics and capabilities"""
        return {
            "supported_formats": self.get_supported_formats(),
            "langchain_version": "0.1.0",
            "loaders": {
                ".pdf": "PyPDFLoader",
                ".txt": "TextLoader",
                ".md": "TextLoader", 
                ".docx": "Docx2txtLoader"
            },
            "features": [
                "Encoding detection for text files",
                "Page-by-page PDF processing",
                "Text cleaning and normalization",
                "Metadata enhancement",
                "Content validation"
            ]
        }


# Global document loader instance
document_loader = EnhancedDocumentLoader()