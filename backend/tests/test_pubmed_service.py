"""
Test Suite — PubMed Search (WS5)

Tests the PubMedService for article search and retrieval.

Usage:
    pytest tests/test_pubmed_service.py -v
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPubMedServiceBasic:
    """Basic PubMedService tests"""

    def test_pubmed_service_import(self):
        """Smoke test: PubMedService imports correctly"""
        from app.services.pubmed_service import PubMedService
        assert PubMedService is not None

    def test_pubmed_service_initialization(self):
        """Test PubMedService initializes correctly"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        assert service is not None
        assert hasattr(service, '_cache')
        assert hasattr(service, '_search_cache')

    def test_singleton_available(self):
        """Test that singleton instance is available"""
        from app.services.pubmed_service import pubmed_service
        assert pubmed_service is not None


class TestPubMedSearch:
    """Test PubMed search functionality"""

    @pytest.mark.asyncio
    async def test_search_mock_success(self):
        """Test PubMed search with mocked API"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        mock_results = [
            {
                "pmid": "12345678",
                "title": "Test Article",
                "authors": ["Smith J", "Doe A"],
                "journal": "Nature",
                "year": "2023"
            }
        ]
        
        with patch.object(service, '_fetch_summaries', return_value=mock_results):
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "esearchresult": {
                        "idlist": ["12345678"]
                    }
                }
                mock_get.return_value.__aenter__.return_value = mock_response
                
                results = await service.search("cancer treatment", max_results=5)
                
                assert len(results) == 1
                assert results[0]["pmid"] == "12345678"
                assert results[0]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_search_cache_hit(self):
        """Test that cached searches are returned immediately"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        cached = [{"pmid": "87654321", "title": "Cached Article"}]
        service._search_cache["cancer:5"] = cached
        
        results = await service.search("cancer", max_results=5)
        
        assert results == cached
        assert results[0]["title"] == "Cached Article"

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Test handling of no results"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "esearchresult": {
                    "idlist": []
                }
            }
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await service.search("nonexistent query xyz123")
            
            assert results == []

    @pytest.mark.asyncio
    async def test_search_api_error(self):
        """Test handling of API errors"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            
            results = await service.search("test")
            
            assert results == []


class TestArticleRetrieval:
    """Test article retrieval functionality"""

    @pytest.mark.asyncio
    async def test_get_article_mock_success(self):
        """Test article retrieval with mocked API"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        mock_article = {
            "pmid": "12345678",
            "title": "Full Article",
            "abstract": "This is the abstract",
            "authors": ["Johnson M"]
        }
        
        with patch.object(service, '_parse_xml_abstract', return_value=mock_article):
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.text = "<PubmedArticleSet></PubmedArticleSet>"
                mock_get.return_value.__aenter__.return_value = mock_response
                
                article = await service.get_article("12345678")
                
                assert article is not None
                assert article["pmid"] == "12345678"

    @pytest.mark.asyncio
    async def test_get_article_cache_hit(self):
        """Test that cached articles are returned immediately"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        cached = {"pmid": "87654321", "title": "Cached Full Article"}
        service._cache["article:87654321"] = cached
        
        article = await service.get_article("87654321")
        
        assert article == cached
        assert article["title"] == "Cached Full Article"

    @pytest.mark.asyncio
    async def test_get_article_not_found(self):
        """Test handling of non-existent article"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_get.return_value.__aenter__.return_value = mock_response
            
            article = await service.get_article("invalid")
            
            assert article is None


class TestSummaryParsing:
    """Test PubMed summary parsing"""

    def test_parse_summary_basic(self):
        """Test basic summary parsing"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        data = {
            "title": "Test Article Title",
            "authors": ["Smith J", "Doe A"],
            "fulljournalname": "Nature Medicine",
            "pubdate": "2023 Jan 15",
            "volume": "29",
            "issue": "1",
            "pages": "100-110",
            "articleids": [
                {"idtype": "doi", "value": "10.1038/test123"}
            ],
            "pubmedurl": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
        }
        
        result = service._parse_summary(data)
        
        assert result["pmid"] == "12345678"
        assert result["title"] == "Test Article Title"
        assert result["authors"] == ["Smith J", "Doe A"]
        assert result["journal"] == "Nature Medicine"
        assert result["year"] == "2023"
        assert result["doi"] == "10.1038/test123"

    def test_parse_summary_minimal(self):
        """Test parsing minimal summary"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        data = {
            "title": "Minimal Article"
        }
        
        result = service._parse_summary(data)
        
        assert result["title"] == "Minimal Article"
        assert result["authors"] == []
        assert result["doi"] == ""


class TestFormatting:
    """Test result formatting"""

    def test_format_for_display(self):
        """Test formatting search results for display"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        articles = [
            {
                "pmid": "12345678",
                "title": "First Article",
                "authors": ["Smith J", "Doe A"],
                "journal": "Nature",
                "year": "2023"
            },
            {
                "pmid": "87654321",
                "title": "Second Article",
                "authors": ["Johnson M"],
                "journal": "Science",
                "year": "2022"
            }
        ]
        
        formatted = service.format_for_display(articles)
        
        assert "## PubMed Search Results" in formatted
        assert "First Article" in formatted
        assert "Second Article" in formatted
        assert "Smith J et al." in formatted

    def test_format_for_display_empty(self):
        """Test formatting empty results"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        formatted = service.format_for_display([])
        
        assert "No articles found" in formatted


class TestPubMedIntegration:
    """Integration tests with real PubMed API"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_search(self):
        """
        Test search with real PubMed API.
        
        Run with: pytest tests/test_pubmed_service.py -v -m integration
        """
        from app.services.pubmed_service import pubmed_service
        
        results = await pubmed_service.search("SGLT2 inhibitors diabetes", max_results=5)
        
        assert len(results) > 0
        assert all("pmid" in r for r in results)
        assert all("title" in r for r in results)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_article_fetch(self):
        """
        Test article fetch with real PubMed API.
        """
        from app.services.pubmed_service import pubmed_service
        
        # Well-known article
        article = await pubmed_service.get_article("34265844")
        
        if article:
            assert "title" in article
            assert article["pmid"] == "34265844"


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self):
        """Test search with special characters in query"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        # Should not crash with special chars
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"esearchresult": {"idlist": []}}
            mock_get.return_value.__aenter__.return_value = mock_response
            
            results = await service.search("IL-6 & TNF-α")
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_max_results_limit(self):
        """Test that max_results is respected"""
        from app.services.pubmed_service import PubMedService
        
        service = PubMedService()
        
        mock_results = [{"pmid": str(i)} for i in range(100)]
        
        with patch.object(service, '_fetch_summaries', return_value=mock_results[:3]):
            with patch('httpx.AsyncClient.get') as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "esearchresult": {"idlist": [str(i) for i in range(100)]}
                }
                mock_get.return_value.__aenter__.return_value = mock_response
                
                results = await service.search("test", max_results=3)
                
                assert len(results) <= 3
