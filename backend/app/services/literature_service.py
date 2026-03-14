"""
Literature Service
Handles PDF retrieval and advanced literature operations for PubMed and Semantic Scholar.
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
from app.services.pubmed_service import PubMedService

logger = logging.getLogger(__name__)

class LiteratureService:
    def __init__(self, pubmed_service: Optional[PubMedService] = None):
        self.pubmed = pubmed_service or PubMedService()
        self.sem_scholar_api = "https://api.semanticscholar.org/graph/v1"
    
    async def get_pdf_link(self, pmid: str) -> Optional[str]:
        """
        Attempts to resolve an Open Access PDF link for a PMID.
        Tried:
        1. PubMed Central (PMC) resolution
        2. Semantic Scholar Open Access API
        3. Unpaywall (Fallback)
        """
        # Try PMC first
        pmc_id = await self.pubmed.get_pmcid(pmid)
        if pmc_id:
            # PMC PDF format: https://www.ncbi.nlm.nih.gov/pmc/articles/PMCXXXXX/pdf/
            # However, direct link is often easier via their API or standard pattern
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc_id}/pdf/"

        # Try Semantic Scholar
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                # https://api.semanticscholar.org/graph/v1/paper/PMID:XXXXXX?fields=openAccessPdf
                resp = await client.get(
                    f"{self.sem_scholar_api}/paper/PMID:{pmid}",
                    params={"fields": "openAccessPdf"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    pdf_data = data.get("openAccessPdf")
                    if pdf_data and pdf_data.get("url"):
                        return pdf_data["url"]
            except Exception as e:
                logger.error(f"Semantic Scholar PDF resolution failed for {pmid}: {e}")

        # Try Unpaywall (Free, no key required for low volume)
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"https://api.unpaywall.org/v2/pmid/{pmid}",
                    params={"email": "research-bot@benchside.com"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    best_oa = data.get("best_oa_location")
                    if best_oa and best_oa.get("url_for_pdf"):
                        return best_oa["url_for_pdf"]
        except Exception as e:
            logger.error(f"Unpaywall PDF resolution failed for {pmid}: {e}")

        return None

    async def fetch_pdf_bytes(self, pdf_url: str) -> bytes:
        """Fetch PDF bytes from a direct URL"""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(pdf_url)
            if resp.status_code == 200:
                return resp.content
            raise Exception(f"Failed to fetch PDF: {resp.status_code}")

# Factory
def get_literature_service() -> LiteratureService:
    from app.services.pubmed_service import get_pubmed_service
    return LiteratureService(pubmed_service=get_pubmed_service())
