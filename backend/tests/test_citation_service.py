"""
Test Suite — Citation Manager (WS4)

Tests the CitationService for DOI/PMID resolution and formatting.

Usage:
    pytest tests/test_citation_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCitationServiceBasic:
    """Basic CitationService tests"""

    def test_citation_service_import(self):
        """Smoke test: CitationService imports correctly"""
        from app.services.citation_service import CitationService
        assert CitationService is not None

    def test_citation_service_initialization(self):
        """Test CitationService initializes correctly"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        assert service is not None
        assert hasattr(service, '_cache')
        assert isinstance(service._cache, dict)

    def test_singleton_available(self):
        """Test that singleton instance is available"""
        from app.services.citation_service import citation_service
        assert citation_service is not None


class TestDOIResolution:
    """Test DOI resolution via CrossRef"""

    @pytest.mark.asyncio
    async def test_resolve_doi_mock_success(self):
        """Test DOI resolution with mocked API"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        mock_metadata = {
            "authors": ["Smith J", "Doe A"],
            "title": "Test Article",
            "journal": "Nature",
            "year": "2023",
            "volume": "10",
            "issue": "2",
            "pages": "100-200",
            "doi": "10.1038/test123",
            "source": "crossref"
        }
        
        with patch.object(service, '_parse_crossref_metadata', return_value=mock_metadata):
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "ok",
                    "message": {"title": ["Test"]}
                }
                mock_get.return_value.__aenter__.return_value = mock_response
                
                result = await service.resolve_doi("10.1038/test123")
                
                assert result is not None
                assert result["doi"] == "10.1038/test123"

    @pytest.mark.asyncio
    async def test_resolve_doi_cache_hit(self):
        """Test that cached DOIs are returned immediately"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        # Pre-populate cache
        cached = {"title": "Cached Article", "doi": "10.1000/cached"}
        service._cache["doi:10.1000/cached"] = cached
        
        result = await service.resolve_doi("10.1000/cached")
        
        assert result == cached
        assert result["title"] == "Cached Article"

    @pytest.mark.asyncio
    async def test_resolve_doi_not_found(self):
        """Test handling of non-existent DOI"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await service.resolve_doi("10.1000/invalid")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_resolve_doi_cleans_prefix(self):
        """Test that DOI prefix is cleaned"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        # Should work with various DOI formats
        dois_to_test = [
            "10.1038/test",
            "https://doi.org/10.1038/test",
            "doi:10.1038/test"
        ]
        
        for doi in dois_to_test:
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 404  # Will fail but we're testing the URL
                mock_get.return_value.__aenter__.return_value = mock_response
                
                await service.resolve_doi(doi)
                
                # Check that the request was made with cleaned DOI
                call_args = mock_get.call_args
                assert "10.1038/test" in call_args[0][0]


class TestPMIDResolution:
    """Test PMID resolution via PubMed"""

    @pytest.mark.asyncio
    async def test_resolve_pmid_mock_success(self):
        """Test PMID resolution with mocked API"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        mock_metadata = {
            "authors": ["Johnson M"],
            "title": "PubMed Test",
            "journal": "Science",
            "year": "2022",
            "pmid": "12345678",
            "source": "pubmed"
        }
        
        with patch.object(service, '_parse_pubmed_metadata', return_value=mock_metadata):
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "result": {
                        "12345678": {"title": "Test"}
                    }
                }
                mock_get.return_value.__aenter__.return_value = mock_response
                
                result = await service.resolve_pmid("12345678")
                
                assert result is not None
                assert result["pmid"] == "12345678"

    @pytest.mark.asyncio
    async def test_resolve_pmid_cache_hit(self):
        """Test that cached PMIDs are returned immediately"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        cached = {"title": "Cached PMID", "pmid": "87654321"}
        service._cache["pmid:87654321"] = cached
        
        result = await service.resolve_pmid("87654321")
        
        assert result == cached


class TestCitationFormatting:
    """Test citation formatting in different styles"""

    def test_format_apa_single_author(self):
        """Test APA format with single author"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        metadata = {
            "authors": ["Smith J"],
            "title": "Test Article",
            "journal": "Nature",
            "year": "2023",
            "volume": "10",
            "doi": "10.1038/test"
        }
        
        citation = service.format_citation(metadata, style="apa")
        
        assert "Smith J" in citation
        assert "(2023)" in citation
        assert "Test Article" in citation

    def test_format_apa_multiple_authors(self):
        """Test APA format with multiple authors"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        metadata = {
            "authors": ["Smith J", "Doe A", "Johnson M"],
            "title": "Multi-Author Paper",
            "journal": "Science",
            "year": "2022",
            "doi": "10.1126/test"
        }
        
        citation = service.format_citation(metadata, style="apa")
        
        assert "Smith J, et al." in citation

    def test_format_vancouver(self):
        """Test Vancouver format"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        metadata = {
            "authors": ["Smith J", "Doe A"],
            "title": "Vancouver Test",
            "journal": "BMJ",
            "year": "2021",
            "volume": "375",
            "pages": "100-110"
        }
        
        citation = service.format_citation(metadata, style="vancouver")
        
        assert "Smith J" in citation
        assert "2021" in citation

    def test_format_bibtex(self):
        """Test BibTeX format"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        metadata = {
            "authors": ["Smith J", "Doe A"],
            "title": "BibTeX Test",
            "journal": "Cell",
            "year": "2020",
            "doi": "10.1016/test"
        }
        
        bibtex = service.format_citation(metadata, style="bibtex")
        
        assert "@article" in bibtex
        assert "author=" in bibtex
        assert "title={BibTeX Test}" in bibtex
        assert "year={2020}" in bibtex

    def test_format_bibtex_file(self):
        """Test generating complete .bib file"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        citations = [
            {
                "authors": ["Smith J"],
                "title": "First Paper",
                "journal": "Nature",
                "year": "2023"
            },
            {
                "authors": ["Doe A"],
                "title": "Second Paper",
                "journal": "Science",
                "year": "2022"
            }
        ]
        
        bib_content = service.generate_bibtex_file(citations)
        
        assert "@article" in bib_content
        assert "First Paper" in bib_content
        assert "Second Paper" in bib_content


class TestExtraction:
    """Test DOI/PMID extraction from text"""

    @pytest.mark.asyncio
    async def test_extract_doi_from_text(self):
        """Test DOI extraction"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        text = """
        According to Smith et al. (2023), this is important.
        See https://doi.org/10.1038/s41586-021-03819-2 for details.
        Also check doi:10.1126/science.abc123
        """
        
        with patch.object(service, 'resolve_doi') as mock_resolve:
            mock_resolve.return_value = {"title": "Test"}
            
            citations = await service.extract_and_resolve(text)
            
            assert mock_resolve.call_count >= 1

    @pytest.mark.asyncio
    async def test_extract_pmid_from_text(self):
        """Test PMID extraction"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        text = """
        Previous studies (PMID: 12345678) have shown...
        Another reference PMID 87654321 supports this.
        """
        
        with patch.object(service, 'resolve_pmid') as mock_resolve:
            mock_resolve.return_value = {"title": "PubMed Test"}
            
            citations = await service.extract_and_resolve(text)
            
            assert mock_resolve.call_count >= 1


class TestCitationServiceIntegration:
    """Integration tests with real APIs (optional)"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resolve_real_doi(self):
        """
        Test DOI resolution with real CrossRef API.
        
        Run with: pytest tests/test_citation_service.py -v -m integration
        """
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        # Real DOI from a known paper
        result = await service.resolve_doi("10.1038/s41586-021-03819-2")
        
        if result:
            assert "title" in result
            assert len(result.get("authors", [])) > 0

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resolve_real_pmid(self):
        """
        Test PMID resolution with real PubMed API.
        """
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        # Real PMID
        result = await service.resolve_pmid("34265844")
        
        if result:
            assert "title" in result
            assert result.get("pmid") == "34265844"


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_format_empty_metadata(self):
        """Test formatting with empty metadata"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        citation = service.format_citation({}, style="apa")
        assert citation == ""

    def test_format_missing_fields(self):
        """Test formatting with missing fields"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        metadata = {"title": "Only Title"}
        citation = service.format_citation(metadata, style="apa")
        
        # Should not crash, should produce something
        assert "Only Title" in citation

    def test_invalid_doi_format(self):
        """Test handling of invalid DOI format"""
        from app.services.citation_service import CitationService
        
        service = CitationService()
        
        # Invalid DOI that doesn't match pattern
        import re
        assert not re.match(r'^10\.\d{4,9}/', "not-a-doi")
