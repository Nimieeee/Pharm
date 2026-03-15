import logging
import httpx
from typing import List, Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class SemanticScholarService:
    """
    Service for interacting with the Semantic Scholar API.
    """
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.SEMANTIC_SCHOLAR_API_KEY
        self.timeout = 30.0
        
    async def search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search Semantic Scholar for papers.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of dictionaries containing paper metadata
        """
        if not query:
            return []
            
        url = f"{self.BASE_URL}/paper/search"
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,authors,year,abstract,citationCount,externalIds,venue,url,openAccessPdf"
        }
        
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
            
        results = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code == 429:
                    logger.error("Semantic Scholar API rate limit reached (429)")
                    return []
                    
                if response.status_code != 200:
                    logger.error(f"Semantic Scholar API error: {response.status_code} - {response.text}")
                    return []
                    
                data = response.json()
                for paper in data.get("data", []):
                    if not paper:
                        continue
                        
                    # Extract external IDs
                    ext_ids = paper.get("externalIds", {})
                    pmid = ext_ids.get("PubMed")
                    doi = ext_ids.get("DOI")
                    
                    # Format authors as "Last, F."
                    authors_list = []
                    for author in paper.get("authors", []):
                        name = author.get("name", "")
                        if name:
                            parts = name.split()
                            if len(parts) >= 2:
                                last_name = parts[-1]
                                first_initial = parts[0][0] + "." if parts[0] else ""
                                authors_list.append(f"{last_name}, {first_initial}")
                            else:
                                authors_list.append(name)
                    
                    author_str = ", ".join(authors_list) or "Unknown Authors"
                    
                    # Check for open access PDF
                    oa_pdf = paper.get("openAccessPdf")
                    pdf_url = oa_pdf.get("url") if oa_pdf else None
                    
                    result = {
                        "id": paper.get("paperId"),
                        "title": paper.get("title", "No Title"),
                        "abstract": paper.get("abstract") or "No abstract available.",
                        "authors": authors_list if authors_list else ["Unknown Authors"],
                        "journal": paper.get("venue", ""),
                        "year": str(paper.get("year", "")) if paper.get("year") else "",
                        "url": paper.get("url", ""),
                        "pdf_url": pdf_url,
                        "pmid": pmid,
                        "doi": doi,
                        "citation_count": paper.get("citationCount", 0),
                        "pdf_available": bool(pdf_url),
                        "source": "Semantic Scholar"
                    }
                    results.append(result)
                    
            return results
        except Exception as e:
            logger.error(f"Semantic Scholar search failed: {e}")
            return []

    async def get_paper(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch details for a specific paper by ID.
        """
        if not paper_id:
            return None
            
        url = f"{self.BASE_URL}/paper/{paper_id}"
        params = {
            "fields": "title,authors,year,abstract,citationCount,externalIds,venue,url,openAccessPdf"
        }
        
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params, headers=headers)
                
                if response.status_code != 200:
                    logger.error(f"Semantic Scholar fetch failed: {response.status_code}")
                    return None
                    
                paper = response.json()
                # Similar mapping logic as search
                ext_ids = paper.get("externalIds", {})
                pmid = ext_ids.get("PubMed")
                doi = ext_ids.get("DOI")
                
                authors_list = [a.get("name", "") for a in paper.get("authors", [])]
                
                return {
                    "id": paper.get("paperId"),
                    "title": paper.get("title"),
                    "abstract": paper.get("abstract"),
                    "authors": authors_list if authors_list else ["Unknown Author"],
                    "journal": paper.get("venue"),
                    "year": str(paper.get("year", "")) if paper.get("year") else "",
                    "url": paper.get("url"),
                    "pmid": pmid,
                    "doi": doi,
                    "citation_count": paper.get("citationCount", 0),
                    "source": "Semantic Scholar"
                }
        except Exception as e:
            logger.error(f"Semantic Scholar get_paper failed: {e}")
            return None

# Singleton instance
semanticscholar_service = SemanticScholarService()
