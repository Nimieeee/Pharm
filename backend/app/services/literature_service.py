import httpx
import logging
import asyncio
from typing import Optional, Dict, Any, List
from app.services.pubmed_service import pubmed_service
from app.services.semanticscholar_service import semanticscholar_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class LiteratureService:
    """
    Service for coordinating literature-related operations across multiple sources.
    """
    def __init__(self):
        self.pubmed = pubmed_service
        self.scholar = semanticscholar_service

    async def search_all(self, query: str, max_results: int = 20, year_from: Optional[int] = None, year_to: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search both PubMed and Semantic Scholar, aggregating and de-duplicating results.
        """
        # Run searches in parallel
        pubmed_task = self.pubmed.search(query, max_results, year_from, year_to)
        scholar_task = self.scholar.search(query, max_results)
        
        pubmed_results, scholar_results = await asyncio.gather(pubmed_task, scholar_task)
        
        # Aggregate results
        combined = []
        seen_dois = set()
        seen_pmids = set()
        
        # Helper to add results while avoiding duplicates
        def add_result(res):
            doi = res.get("doi")
            pmid = res.get("pmid")
            
            # De-duplicate by DOI or PMID
            if doi and doi.lower() in seen_dois:
                return
            if pmid and pmid in seen_pmids:
                return
                
            if doi: seen_dois.add(doi.lower())
            if pmid: seen_pmids.add(pmid)
            combined.append(res)

        # Interleave results (priority to Semantic Scholar for general discovery)
        for i in range(max(len(pubmed_results), len(scholar_results))):
            if i < len(scholar_results):
                add_result(scholar_results[i])
            if i < len(pubmed_results):
                add_result(pubmed_results[i])
                
        return combined[:max_results]

    async def get_pdf_link(self, pmid: str = None, doi: str = None) -> Optional[str]:
        """
        Attempts to resolve an Open Access PDF link using multiple providers.
        """
        # 1. Try Semantic Scholar
        if pmid or doi:
            paper_id = f"PMID:{pmid}" if pmid else f"DOI:{doi}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    headers = {"x-api-key": settings.SEMANTIC_SCHOLAR_API_KEY} if settings.SEMANTIC_SCHOLAR_API_KEY else {}
                    resp = await client.get(
                        f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}",
                        params={"fields": "openAccessPdf"},
                        headers=headers
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        pdf_data = data.get("openAccessPdf")
                        if pdf_data and pdf_data.get("url"):
                            return pdf_data["url"]
                except Exception as e:
                    logger.error(f"Semantic Scholar PDF resolution failed: {e}")

        # 2. Try Unpaywall
        if doi:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(
                        f"https://api.unpaywall.org/v2/{doi}",
                        params={"email": "research-bot@benchside.com"}
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        best_oa = data.get("best_oa_location")
                        if best_oa and best_oa.get("url_for_pdf"):
                            return best_oa["url_for_pdf"]
            except Exception as e:
                logger.error(f"Unpaywall PDF resolution failed: {e}")

        # 3. If only PMID, try to resolve to DOI first
        if pmid and not doi:
            article = await self.pubmed.get_article(pmid)
            if article and article.get("doi"):
                return await self.get_pdf_link(doi=article["doi"])

        return None

    async def fetch_pdf_bytes(self, pdf_url: str) -> bytes:
        """Fetch PDF bytes from a direct URL with robust error handling"""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                }
                resp = await client.get(pdf_url, headers=headers)
                
                if resp.status_code == 200:
                    content_type = resp.headers.get("Content-Type", "").lower()
                    if "application/pdf" in content_type:
                        return resp.content
                    else:
                        logger.error(f"Failed to fetch PDF from {pdf_url}: URL returned {content_type} instead of PDF")
                        # Many publishers (Nature, Springer) serve an HTML challenge page instead of PDF
                        raise Exception("PDF download unavailable: The publisher's site is currently restricted or requiring a bot check.")
                
                logger.error(f"Failed to fetch PDF from {pdf_url}: HTTP {resp.status_code}")
                # Log a snippet of the error page if it's not a PDF
                try:
                    error_body = resp.text[:200]
                    logger.error(f"Error body snippet: {error_body}")
                except:
                    pass
                
                if resp.status_code == 403:
                    raise Exception("Access Denied: This PDF is behind a paywall or institutional login.")
                elif resp.status_code == 404:
                    raise Exception("Not Found: The PDF file could not be located on the publisher's server.")
                else:
                    raise Exception(f"HTTP {resp.status_code}: PDF download restricted or unavailable")
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching PDF from {pdf_url}: {str(e)}")
            raise Exception(f"Network error while connecting to publisher: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching PDF from {pdf_url}: {str(e)}")
            raise e

# Singleton Instance
literature_service = LiteratureService()

def get_literature_service() -> LiteratureService:
    return literature_service
