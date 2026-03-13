"""
PDF Full-Text Extraction Service
Downloads and extracts text from Open Access PDFs via Semantic Scholar Links.
"""

import logging
import httpx
import tempfile
import os
import asyncio
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pypdf import PdfReader

logger = logging.getLogger(__name__)

@dataclass
class PDFArticle:
    """Extracted content from a PDF article"""
    url: str
    paper_id: Optional[str]
    title: Optional[str] 
    full_text: str
    page_count: int
    metadata: Dict[str, Any]

class PDFFullTextService:
    """
    Downloads open-access PDFs and extracts text content.
    Includes rate limiting, user-agent spoofing, and temp file management.
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
    
    async def fetch_and_extract(self, url: str, paper_id: Optional[str] = None, title: Optional[str] = None) -> Optional[PDFArticle]:
        """
        Download PDF from URL and extract text contents.
        
        Args:
            url: URL to the PDF file
            paper_id: Optional tracking ID (e.g., Semantic Scholar Paper ID)
            title: Optional title for tracking
            
        Returns:
            PDFArticle object with extracted text or None if failed
        """
        temp_path = None
        try:
            # Download PDF to a temporary file
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=30.0) as client:
                response = await client.get(url)
                
                if response.status_code != 200:
                    logger.warning(f"PDF download failed for {url}: HTTP {response.status_code}")
                    return None
                    
                # Create temporary file
                fd, temp_path = tempfile.mkstemp(suffix=".pdf")
                with os.fdopen(fd, 'wb') as f:
                    f.write(response.content)
            
            # Run extraction in a separate thread to avoid blocking event loop
            return await asyncio.to_thread(self._extract_text_from_file, temp_path, url, paper_id, title)
            
        except httpx.TimeoutException:
            logger.warning(f"PDF download timeout for {url}")
            return None
        except Exception as e:
            logger.error(f"Error fetching PDF from {url}: {str(e)}")
            return None
        finally:
            # Clean up temporary file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp PDF file {temp_path}: {e}")
    
    def _extract_text_from_file(self, file_path: str, url: str, paper_id: Optional[str], title: Optional[str]) -> Optional[PDFArticle]:
        """Synchronous text extraction using pypdf"""
        try:
            reader = PdfReader(file_path)
            
            if len(reader.pages) == 0:
                logger.warning(f"Extracted 0 pages from PDF at {url}")
                return None
                
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {i+1} ---\n{page_text}")
            
            full_text = "\n\n".join(text_parts)
            
            # Fallback if pypdf returns empty strings for all pages
            if not full_text.strip():
                logger.warning(f"PDF extraction yielded empty text for {url}")
                return None
                
            metadata = dict(reader.metadata) if reader.metadata else {}
            
            return PDFArticle(
                url=url,
                paper_id=paper_id,
                title=title or metadata.get("/Title"),
                full_text=full_text,
                page_count=len(reader.pages),
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path} ({url}): {e}")
            return None
