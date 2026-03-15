"""
PubMed Search Service

Direct integration with PubMed E-utilities API for searching biomedical literature.
All APIs are free and require no API key.

API Documentation:
https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime


class PubMedService:
    """
    PubMed search and retrieval service.
    
    Features:
    - Search PubMed via E-utilities API
    - Fetch full article metadata
    - Abstract retrieval
    - No API key required (free NCBI service)
    """
    
    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self):
        """Initialize PubMedService"""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._search_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    async def search(
        self, 
        query: str, 
        max_results: int = 20,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        use_history: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search PubMed for articles.
        
        Args:
            query: Search query (supports MeSH terms, Boolean operators)
            max_results: Maximum number of results to return (default: 20)
            year_from: Filter results from this year (inclusive)
            year_to: Filter results to this year (inclusive)
            use_history: Use NCBI search history for large result sets
            
        Returns:
            List of article metadata dictionaries
        """
        # Check cache first
        cache_key = f"{query}:{max_results}:{year_from}:{year_to}"
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]
        
        # Build date filter if provided
        date_filter = ""
        if year_from and year_to:
            date_filter = f" AND ({year_from}[PDAT] : {year_to}[PDAT])"
        elif year_from:
            date_filter = f" AND ({year_from}[PDAT] : 3000[PDAT])"
        elif year_to:
            date_filter = f" AND (1800[PDAT] : {year_to}[PDAT])"
        
        # Sanitize query: remove characters like [] that might be interpreted as tags unless they look like [PDAT]
        sanitized_query = query.replace("[", " ").replace("]", " ").strip()
        # Restore PDAT tags if they were there (very rough)
        if year_from or year_to:
            # We add them specifically below
            pass

        full_query = f"{sanitized_query}{date_filter}" if date_filter else sanitized_query
        
        headers = {
            "User-Agent": "Benchside/1.0 (https://benchside.com; mailto:research-bot@benchside.com)",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
                # Step 1: ESearch - get PMIDs
                print(f"🔍 Searching PubMed for: {full_query}")
                search_response = await client.get(
                    f"{self.BASE}/esearch.fcgi",
                    params={
                        "db": "pubmed",
                        "term": full_query,
                        "retmax": max_results,
                        "retmode": "json",
                        "sort": "relevance",
                        "tool": "benchside",
                        "email": "research-bot@benchside.com"
                    }
                )
                
                if search_response.status_code != 200:
                    print(f"❌ PubMed ESearch failed: {search_response.status_code}")
                    return []
                
                search_data = search_response.json()
                pmids = search_data.get("esearchresult", {}).get("idlist", [])
                
                if not pmids:
                    return []
                
                # Step 2: ESummary - get metadata for PMIDs
                summaries = await self._fetch_summaries(pmids)
                
                # Cache results
                self._search_cache[cache_key] = summaries
                
                return summaries
                
        except Exception as e:
            print(f"❌ PubMed search failed for '{query}': {e}")
            return []
    
    async def _fetch_summaries(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch summaries for a list of PMIDs"""
        if not pmids:
            return []
        
        # NCBI limits to 200 IDs per request
        batches = [pmids[i:i+200] for i in range(0, len(pmids), 200)]
        all_summaries = []
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            for batch in batches:
                try:
                    response = await client.get(
                        f"{self.BASE}/esummary.fcgi",
                        params={
                            "db": "pubmed",
                            "id": ",".join(batch),
                            "retmode": "json"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get("result", {})
                        
                        for pmid in batch:
                            if pmid in results:
                                summary = self._parse_summary(results[pmid])
                                all_summaries.append(summary)
                                
                except Exception as e:
                    print(f"❌ Failed to fetch summaries for batch: {e}")
        
        return all_summaries
    
    async def get_article(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Get full article details including abstract.
        
        Args:
            pmid: PubMed ID
            
        Returns:
            Dict with full article metadata including abstract
        """
        # Check cache
        cache_key = f"article:{pmid}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            async with httpx.AsyncClient(timeout=15.0, headers={
                "User-Agent": "Benchside/1.0 (Pharmacology AI Research Platform)"
            }) as client:
                # Fetch full record with abstract
                response = await client.get(
                    f"{self.BASE}/efetch.fcgi",
                    params={
                        "db": "pubmed",
                        "id": pmid,
                        "rettype": "abstract",
                        "retmode": "xml"
                    }
                )
                
                if response.status_code == 200:
                    # Parse XML response
                    article = self._parse_xml_abstract(response.text, pmid)
                    if article:
                        self._cache[cache_key] = article
                        return article
                        
                # Fallback to summary if efetch fails
                summary = await self.resolve_pmid(pmid)
                if summary:
                    self._cache[cache_key] = summary
                    return summary
                    
        except Exception as e:
            print(f"❌ PubMed article fetch failed for {pmid}: {e}")
        
        return None

    async def get_pmcid(self, pmid: str) -> Optional[str]:
        """
        Resolve PMCID from PMID via ID Converter API.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
                    params={
                        "ids": pmid,
                        "format": "json",
                        "tool": "benchside",
                        "email": "research-bot@benchside.com"
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    records = data.get("records", [])
                    if records:
                        return records[0].get("pmcid")
        except Exception as e:
            print(f"❌ PMCID resolution failed for {pmid}: {e}")
        return None
    def _parse_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PubMed ESummary response"""
        # Extract authors
        authors = []
        if "authors" in data:
            for author in data["authors"]:
                if isinstance(author, str):
                    authors.append(author)
                elif isinstance(author, dict):
                    name = author.get("name", "")
                    if name:
                        authors.append(name)
        
        # Extract DOI from articleids
        doi = ""
        if "articleids" in data:
            for article_id in data["articleids"]:
                if article_id.get("idtype") == "doi":
                    doi = article_id.get("value", "")
                    break
        
        # Parse publication date
        pubdate = data.get("pubdate", "")
        year = ""
        if pubdate:
            parts = pubdate.split()
            year = parts[0] if parts else ""
        
        # Journal name
        journal = data.get("fulljournalname", data.get("source", ""))
        
        # Abstract preview (first 200 chars)
        full_abstract = data.get("fullabstractname", "")
        abstract_preview = full_abstract[:200] + "..." if len(full_abstract) > 200 else full_abstract
        
        pmid = data.get("pubmedurl", "").split("/")[-1] if "pubmedurl" in data else ""
        
        # Check for PMC ID to indicate PDF availability
        pmc_id = ""
        if "articleids" in data:
            for article_id in data["articleids"]:
                if article_id.get("idtype") == "pmc":
                    pmc_id = article_id.get("value", "")
                    break

        return {
            "id": pmid,
            "pmid": pmid,
            "pmcid": pmc_id,
            "title": data.get("title", ""),
            "authors": authors,
            "journal": journal,
            "year": year,
            "volume": data.get("volume", ""),
            "issue": data.get("issue", ""),
            "pages": data.get("pages", ""),
            "doi": doi,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            "pubdate": pubdate,
            "abstract_preview": abstract_preview,
            "has_abstract": bool(full_abstract),
            "pdf_available": bool(pmc_id),
            "source": "pubmed"
        }
    
    def _parse_xml_abstract(self, xml_text: str, pmid: str) -> Optional[Dict[str, Any]]:
        """Parse PubMed XML efetch response"""
        try:
            import xml.etree.ElementTree as ET
            
            # Remove namespaces for easier parsing
            xml_text = xml_text.replace('xmlns="http://www.ncbi.nlm.nih.gov/pubmed/v1"', '')
            root = ET.fromstring(xml_text)
            
            # Find PubmedArticle
            article_elem = root.find('.//PubmedArticle')
            if article_elem is None:
                return None
            
            # Extract MedlineCitation
            citation = article_elem.find('MedlineCitation')
            if citation is None:
                return None
            
            # Title
            title_elem = citation.find('Article/ArticleTitle')
            title = title_elem.text if title_elem is not None else ""
            
            # Authors
            authors = []
            author_list = citation.findall('Article/AuthorList/Author')
            for author_elem in author_list:
                last = author_elem.find('LastName')
                fore = author_elem.find('ForeName')
                if last is not None:
                    name = last.text
                    if fore is not None:
                        name += f" {fore.text}"
                    authors.append(name)
            
            # Journal
            journal_elem = citation.find('Article/Journal/Title')
            journal = journal_elem.text if journal_elem is not None else ""
            
            # Publication date
            pubdate_elem = citation.find('Article/Journal/JournalIssue/PubDate')
            year = ""
            if pubdate_elem is not None:
                year_elem = pubdate_elem.find('Year')
                if year_elem is not None:
                    year = year_elem.text
            
            # Abstract
            abstract = ""
            abstract_elem = citation.find('Article/Abstract/AbstractText')
            if abstract_elem is not None:
                abstract = abstract_elem.text or ""
            
            # DOI
            doi = ""
            doi_elem = citation.find('Article/ELocationID[@EIdType="doi"]')
            if doi_elem is not None:
                doi = doi_elem.text or ""
            
            return {
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "journal": journal,
                "year": year,
                "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "abstract": abstract,
                "source": "pubmed"
            }
            
        except Exception as e:
            print(f"❌ XML parsing failed: {e}")
            return None
    
    async def resolve_pmid(self, pmid: str) -> Optional[Dict[str, Any]]:
        """Alias for get_article for compatibility with CitationService"""
        return await self.get_article(pmid)
    
    def format_for_display(self, articles: List[Dict[str, Any]]) -> str:
        """
        Format search results for display in chat.
        
        Args:
            articles: List of article metadata
            
        Returns:
            Formatted markdown string
        """
        if not articles:
            return "No articles found."
        
        lines = [f"## PubMed Search Results ({len(articles)} articles)\n"]
        
        for i, article in enumerate(articles[:10], 1):  # Show top 10
            title = article.get("title", "No title")
            authors = article.get("authors", [])
            authors_str = authors[0] + " et al." if len(authors) > 1 else (authors[0] if authors else "Unknown")
            journal = article.get("journal", "")
            year = article.get("year", "")
            pmid = article.get("pmid", "")
            
            lines.append(f"**{i}. {title}**")
            lines.append(f"   - {authors_str}. {journal}. {year}")
            if pmid:
                lines.append(f"   - [PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
            lines.append("")
        
        if len(articles) > 10:
            lines.append(f"*...and {len(articles) - 10} more results*")
        
        return "\n".join(lines)


# Singleton instance
pubmed_service = PubMedService()

def get_pubmed_service() -> PubMedService:
    """Get PubMedService singleton instance"""
    return pubmed_service
