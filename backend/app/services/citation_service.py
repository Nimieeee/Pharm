"""
Citation Manager Service

Resolves DOIs and PMIDs to formatted citations via CrossRef and PubMed APIs.
Supports APA, Vancouver, and BibTeX export formats.

All external APIs are free and require no API key:
- CrossRef API: https://api.crossref.org/
- PubMed E-utilities: https://eutils.ncbi.nlm.nih.gov/
"""

import re
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime


class CitationService:
    """
    Citation resolution and formatting service.
    
    Features:
    - DOI resolution via CrossRef API
    - PMID resolution via PubMed E-utilities
    - Multiple citation styles (APA, Vancouver, BibTeX)
    - Automatic extraction from text
    """
    
    CROSSREF_BASE = "https://api.crossref.org"
    PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    def __init__(self):
        """Initialize CitationService"""
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def resolve_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Resolve DOI to metadata via CrossRef API.
        
        Args:
            doi: DOI string (e.g., "10.1038/s41586-021-03819-2")
            
        Returns:
            Dict with metadata or None if not found
        """
        # Check cache first
        cache_key = f"doi:{doi}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Clean DOI (remove prefix if present)
        doi = doi.replace("https://doi.org/", "").replace("doi:", "").strip()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.CROSSREF_BASE}/works/{doi}",
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "ok":
                        metadata = self._parse_crossref_metadata(data["message"])
                        self._cache[cache_key] = metadata
                        return metadata
                        
        except Exception as e:
            print(f"❌ CrossRef DOI resolution failed for {doi}: {e}")
        
        return None
    
    async def resolve_pmid(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Resolve PMID to metadata via PubMed E-utilities.
        
        Args:
            pmid: PubMed ID string (e.g., "34265844")
            
        Returns:
            Dict with metadata or None if not found
        """
        # Check cache first
        cache_key = f"pmid:{pmid}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        pmid = pmid.strip()
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Fetch summary
                response = await client.get(
                    f"{self.PUBMED_BASE}/esummary.fcgi",
                    params={
                        "db": "pubmed",
                        "id": pmid,
                        "retmode": "json",
                        "retmax": 1
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data and pmid in data["result"]:
                        metadata = self._parse_pubmed_metadata(data["result"][pmid])
                        self._cache[cache_key] = metadata
                        return metadata
                        
        except Exception as e:
            print(f"❌ PubMed PMID resolution failed for {pmid}: {e}")
        
        return None
    
    def _parse_crossref_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse CrossRef API response to standard format"""
        # Extract authors
        authors = []
        if "author" in data:
            for author in data["author"]:
                name_parts = []
                if "given" in author:
                    name_parts.append(author["given"])
                if "family" in author:
                    name_parts.append(author["family"])
                if name_parts:
                    authors.append(" ".join(name_parts))
        
        # Extract title
        title = data.get("title", [""])[0] if isinstance(data.get("title"), list) else data.get("title", "")
        
        # Extract journal
        journal = data.get("container-title", [""])[0] if isinstance(data.get("container-title"), list) else data.get("container-title", "")
        
        # Extract volume, issue, pages
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("page", "")
        
        # Extract year
        published = data.get("published", {})
        year = str(published.get("date-parts", [[None]])[0][0]) if published else ""
        
        # Extract DOI
        doi = data.get("DOI", "")
        
        return {
            "source": "crossref",
            "authors": authors,
            "title": title,
            "journal": journal,
            "year": year,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "doi": doi,
            "url": f"https://doi.org/{doi}",
            "type": data.get("type", "journal-article")
        }
    
    def _parse_pubmed_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PubMed E-utilities response to standard format"""
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
        
        # Extract title
        title = data.get("title", "")
        
        # Extract journal
        journal = data.get("fulljournalname", data.get("source", ""))
        
        # Extract year
        pubdate = data.get("pubdate", "")
        year = pubdate.split()[0] if pubdate else ""
        
        # Extract volume, issue, pages
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("pages", "")
        
        # Extract DOI if available
        doi = ""
        if "doi" in data:
            doi = data["doi"]
        elif "articleids" in data:
            for article_id in data["articleids"]:
                if article_id.get("idtype") == "doi":
                    doi = article_id.get("value", "")
                    break
        
        # Extract PMID
        pmid = data.get("pubmedurl", "").split("/")[-1] if "pubmedurl" in data else ""
        
        return {
            "source": "pubmed",
            "authors": authors,
            "title": title,
            "journal": journal,
            "year": year,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "doi": doi,
            "pmid": pmid,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
            "type": "journal-article"
        }
    
    def format_citation(self, metadata: Dict[str, Any], style: str = "apa") -> str:
        """
        Format citation metadata to string.
        
        Args:
            metadata: Dict from resolve_doi() or resolve_pmid()
            style: Citation style (apa, vancouver, bibtex)
            
        Returns:
            Formatted citation string
        """
        if not metadata:
            return ""
        
        if style.lower() == "apa":
            return self._format_apa(metadata)
        elif style.lower() == "vancouver":
            return self._format_vancouver(metadata)
        elif style.lower() == "bibtex":
            return self._format_bibtex(metadata)
        else:
            return self._format_apa(metadata)
    
    def _format_apa(self, metadata: Dict[str, Any]) -> str:
        """Format as APA 7th edition"""
        authors = metadata.get("authors", [])
        year = metadata.get("year", "n.d.")
        title = metadata.get("title", "")
        journal = metadata.get("journal", "")
        volume = metadata.get("volume", "")
        issue = metadata.get("issue", "")
        pages = metadata.get("pages", "")
        doi = metadata.get("doi", "")
        
        # Format authors
        if len(authors) == 0:
            authors_str = "Unknown author"
        elif len(authors) == 1:
            authors_str = authors[0]
        elif len(authors) == 2:
            authors_str = f"{authors[0]} & {authors[1]}"
        else:
            # 3+ authors: use et al.
            authors_str = f"{authors[0]}, et al."
        
        # Build citation
        parts = [f"{authors_str} ({year})"]
        parts.append(f"{title}")
        
        if journal:
            journal_part = f"<i>{journal}</i>"
            if volume:
                journal_part += f", <i>{volume}</i>"
                if issue:
                    journal_part += f"({issue})"
            if pages:
                journal_part += f", {pages}"
            parts.append(journal_part)
        
        if doi:
            parts.append(f"https://doi.org/{doi}")
        
        return ". ".join(parts) + "."
    
    def _format_vancouver(self, metadata: Dict[str, Any]) -> str:
        """Format as Vancouver style"""
        authors = metadata.get("authors", [])
        year = metadata.get("year", "")
        title = metadata.get("title", "")
        journal = metadata.get("journal", "")
        volume = metadata.get("volume", "")
        issue = metadata.get("issue", "")
        pages = metadata.get("pages", "")
        
        # Format authors (Last FM for first 6, then et al.)
        if len(authors) == 0:
            authors_str = "Unknown"
        elif len(authors) <= 6:
            authors_list = []
            for author in authors:
                parts = author.split()
                if len(parts) >= 2:
                    last = parts[-1]
                    initials = "".join([p[0] for p in parts[:-1]])
                    authors_list.append(f"{last} {initials}")
                else:
                    authors_list.append(author)
            authors_str = ", ".join(authors_list)
        else:
            # More than 6: first 6 + et al
            authors_list = []
            for author in authors[:6]:
                parts = author.split()
                if len(parts) >= 2:
                    last = parts[-1]
                    initials = "".join([p[0] for p in parts[:-1]])
                    authors_list.append(f"{last} {initials}")
                else:
                    authors_list.append(author)
            authors_str = ", ".join(authors_list) + ", et al."
        
        # Build citation
        parts = [authors_str]
        parts.append(f"{title}")
        
        journal_part = f"{journal}"
        if year:
            journal_part += f". {year}"
        if volume:
            journal_part += f";{volume}"
            if issue:
                journal_part += f"({issue})"
        if pages:
            journal_part += f":{pages}"
        
        if journal_part:
            parts.append(journal_part)
        
        return ". ".join(parts) + "."
    
    def _format_bibtex(self, metadata: Dict[str, Any]) -> str:
        """Format as BibTeX entry"""
        # Generate citation key
        authors = metadata.get("authors", [])
        year = metadata.get("year", "")
        title = metadata.get("title", "")
        
        # Create key from first author + year
        if authors and year:
            first_author = authors[0].split()[-1].lower() if authors[0] else "unknown"
            key = f"{first_author}{year}"
        else:
            key = f"ref{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Clean title for key
        key = re.sub(r'[^a-z0-9]', '', key)[:20]
        
        # Build BibTeX
        bibtex = f"@article{{{key},\n"
        
        if authors:
            bibtex += f"  author={{{' and '.join(authors)}}},\n"
        if title:
            bibtex += f"  title={{{title}}},\n"
        if metadata.get("journal"):
            bibtex += f"  journal={{{metadata['journal']}}},\n"
        if year:
            bibtex += f"  year={{{year}}},\n"
        if metadata.get("volume"):
            bibtex += f"  volume={{{metadata['volume']}}},\n"
        if metadata.get("number"):
            bibtex += f"  number={{{metadata['number']}}},\n"
        if metadata.get("pages"):
            bibtex += f"  pages={{{metadata['pages']}}},\n"
        if metadata.get("doi"):
            bibtex += f"  doi={{{metadata['doi']}}},\n"
        if metadata.get("url"):
            bibtex += f"  url={{{metadata['url']}}},\n"
        
        bibtex += "}"
        
        return bibtex
    
    async def extract_and_resolve(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract DOIs and PMIDs from text and resolve them.
        
        Args:
            text: Text to search for citations
            
        Returns:
            List of resolved citation metadata
        """
        citations = []
        
        # DOI pattern: 10.xxxx/xxxx
        doi_pattern = r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b'
        dois = re.findall(doi_pattern, text, re.IGNORECASE)
        
        # PMID pattern: 5-8 digit numbers (common in PubMed citations)
        pmid_pattern = r'\bPMID[:\s]?(\d{5,8})\b'
        pmids = re.findall(pmid_pattern, text, re.IGNORECASE)
        
        # Resolve DOIs
        for doi in dois:
            metadata = await self.resolve_doi(doi)
            if metadata:
                citations.append(metadata)
        
        # Resolve PMIDs
        for pmid in pmids:
            metadata = await self.resolve_pmid(pmid)
            if metadata:
                citations.append(metadata)
        
        return citations
    
    def generate_bibtex_file(self, citations: List[Dict[str, Any]]) -> str:
        """
        Generate complete .bib file content from citations.
        
        Args:
            citations: List of citation metadata
            
        Returns:
            Complete BibTeX file content
        """
        entries = []
        for citation in citations:
            bibtex = self._format_bibtex(citation)
            entries.append(bibtex)
        
        return "\n\n".join(entries)


# Singleton instance
citation_service = CitationService()
