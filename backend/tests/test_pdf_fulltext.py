"""
Tests for PDF Full-Text Extraction Service
"""

import pytest
import os
from app.services.pdf_fulltext import PDFFullTextService, PDFArticle


class TestPDFFullTextService:
    """Test PDF downloading and text extraction"""
    
    @pytest.mark.asyncio
    async def test_fetch_pdf_success(self):
        """Test fetching a known valid open-access PDF"""
        service = PDFFullTextService()
        
        # We need a stable public PDF URL for testing.
        # W3C test PDF or arXiv are usually reliable.
        # Using a minimal arXiv paper PDF.
        url = "https://arxiv.org/pdf/1706.03762.pdf" # Attention is all you need
        
        result = await service.fetch_and_extract(url, paper_id="arxiv:1706.03762")
        
        assert result is not None, "Failed to download/extract PDF"
        assert isinstance(result, PDFArticle)
        assert result.page_count > 0, "PDF should have pages"
        assert len(result.full_text) > 1000, "Should have extracted some text"
        assert "Attention Is All You Need" in result.full_text or "Attention Is All You Need" in result.full_text.replace("\n", " "), "Should contain paper title in text"
        assert result.url == url
        assert result.paper_id == "arxiv:1706.03762"
        
    @pytest.mark.asyncio
    async def test_fetch_pdf_invalid_url(self):
        """Test handling of invalid URL or 404"""
        service = PDFFullTextService()
        
        url = "https://arxiv.org/pdf/invalid_not_exist.pdf"
        
        result = await service.fetch_and_extract(url)
        
        assert result is None, "Should return None for invalid PDF URL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
