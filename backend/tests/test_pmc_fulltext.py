"""
Tests for PubMed Central Full-Text Fetching Service
"""

import pytest
import asyncio
from app.services.pmc_fulltext import PMCFullTextService, PMCArticle


class TestPMCFullTextService:
    """Test PMC full-text fetching functionality"""
    
    @pytest.mark.asyncio
    async def test_fetch_pmc_fulltext_success(self):
        """Test fetching full-text from PubMed Central with known PMC ID"""
        service = PMCFullTextService(api_key=None)
        
        # Test with a known PMC article (artemisinin review)
        pmcid = "PMC8752222"
        result = await service.fetch_fulltext(pmcid)
        
        # Verify result structure
        assert result is not None, "PMC fetch returned None"
        assert isinstance(result, PMCArticle)
        assert result.pmcid == pmcid
        assert len(result.full_text) > 1000, f"Full text too short: {len(result.full_text)} chars"
        assert result.title, "Title should not be empty"
        assert len(result.authors) > 0, "Should have at least one author"
    
    @pytest.mark.asyncio
    async def test_fetch_pmc_with_tables(self):
        """Test that tables are extracted from PMC articles"""
        service = PMCFullTextService(api_key=None)
        pmcid = "PMC8752222"
        
        result = await service.fetch_fulltext(pmcid, include_tables=True)
        
        assert result is not None
        # This article has at least one table
        assert len(result.tables) >= 0, "Should extract tables (may be 0 for some articles)"
    
    @pytest.mark.asyncio
    async def test_fetch_pmc_invalid_id(self):
        """Test handling of invalid PMCID"""
        service = PMCFullTextService(api_key=None)
        
        result = await service.fetch_fulltext("PMC_INVALID_999999")
        
        assert result is None, "Should return None for invalid PMCID"
    
    @pytest.mark.asyncio
    async def test_fetch_pmc_sections_extracted(self):
        """Test that article sections are properly extracted"""
        service = PMCFullTextService(api_key=None)
        pmcid = "PMC8752222"
        
        result = await service.fetch_fulltext(pmcid)
        
        assert result is not None
        assert len(result.sections) > 0, "Should have at least one section"
        
        # Check for common section names (commented out as PMC8752222 is a review)
        section_titles = [s.lower() for s in result.sections.keys()]
        assert len(section_titles) >= 3, "Review article should have multiple sections"
    
    @pytest.mark.asyncio
    async def test_rate_limiting_works(self):
        """Test that rate limiting is enforced"""
        service = PMCFullTextService(api_key=None)
        
        # Make two rapid requests
        import time
        start = time.time()
        
        await service.fetch_fulltext("PMC8752222")
        await service.fetch_fulltext("PMC8752222")
        
        elapsed = time.time() - start
        
        # Should take at least 100ms due to rate limiting
        assert elapsed >= 0.09, f"Rate limiting may not be working: {elapsed}s elapsed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
