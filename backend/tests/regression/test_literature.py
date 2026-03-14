import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

# Mock settings BEFORE importing services that use them
mock_settings = MagicMock()
mock_settings.SEMANTIC_SCHOLAR_API_KEY = "dummy_key"
with patch("app.core.config.settings", mock_settings):
    from app.services.literature_service import LiteratureService
    from app.services.pubmed_service import pubmed_service
    from app.services.semanticscholar_service import semanticscholar_service

@pytest.mark.asyncio
async def test_literature_service_author_format():
    """
    Test that LiteratureService returns authors as a list of strings,
    not a single string, even when aggregated from Semantic Scholar.
    """
    with patch("app.services.pubmed_service.pubmed_service.search", new_callable=AsyncMock) as mock_pubmed, \
         patch("app.services.semanticscholar_service.semanticscholar_service.search", new_callable=AsyncMock) as mock_scholar:
        
        # Mock PubMed returning a list of strings
        mock_pubmed.return_value = [{
            "pmid": "123",
            "title": "PubMed Paper",
            "authors": ["Author A", "Author B"],
            "source": "pubmed"
        }]
        
        # Mock Semantic Scholar - this is what we fixed
        # It should now return a list, not "Author C, Author D"
        mock_scholar.return_value = [{
            "id": "ss1",
            "title": "Scholar Paper",
            "authors": ["Author C", "Author D"],
            "source": "Semantic Scholar"
        }]
        
        service = LiteratureService()
        results = await service.search_all("test query", max_results=2)
        
        assert len(results) == 2
        for res in results:
            assert isinstance(res["authors"], list), f"Authors should be a list in {res['source']}"
            assert len(res["authors"]) > 0
            assert isinstance(res["authors"][0], str)

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

if __name__ == "__main__":
    # Manual run helper
    import sys
    import os
    sys.path.append(os.getcwd())
    asyncio.run(test_literature_service_author_format())
    print("✅ Literature author format test passed!")
