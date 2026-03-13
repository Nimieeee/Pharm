"""
PubMed Central Full-Text Fetching Service
Fetches complete full-text XML from PMC and extracts structured content.
"""

import logging
import httpx
import xml.etree.ElementTree as ET
import asyncio
from typing import Optional, Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PMCArticle:
    """Structured PMC article content"""
    pmcid: str
    pmid: Optional[str]
    title: str
    authors: List[str]
    journal: str
    year: str
    full_text: str
    sections: Dict[str, str]  # section_title -> section_text
    tables: List[Dict[str, Any]]  # List of table data
    doi: Optional[str]

class PMCFullTextService:
    """
    Fetches and parses full-text articles from PubMed Central.
    Uses NCBI E-utilities API with proper rate limiting.
    """
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    RATE_LIMIT = 10  # requests per second (with API key)
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._request_count = 0
        self._last_request_time = 0.0
    
    async def fetch_fulltext(
        self, 
        pmcid: str,
        include_tables: bool = True
    ) -> Optional[PMCArticle]:
        """
        Fetch full-text XML from PubMed Central and parse it.
        
        Args:
            pmcid: PubMed Central ID (e.g., "PMC8752222")
            include_tables: Whether to extract table data
            
        Returns:
            PMCArticle with structured content, or None if fetch fails
        """
        try:
            # Clean PMCID (remove "PMC" prefix if present)
            pmcid_clean = pmcid.replace("PMC", "")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Fetch full-text XML
                url = f"{self.BASE_URL}/efetch.fcgi"
                params = {
                    "db": "pmc",
                    "id": pmcid_clean,
                    "retmode": "xml"
                }
                
                if self.api_key:
                    params["api_key"] = self.api_key
                
                await self._rate_limit()
                response = await client.get(url, params=params)
                
                if response.status_code != 200:
                    logger.warning(f"PMC fetch failed for {pmcid}: HTTP {response.status_code}")
                    return None
                
                # Parse XML
                root = ET.fromstring(response.text)
                
                # Check for errors in the XML
                if root.find(".//error") is not None:
                    return None
                    
                return self._parse_pmc_xml(root, pmcid_clean, include_tables)
                
        except httpx.TimeoutException:
            logger.warning(f"PMC fetch timeout for {pmcid}")
            return None
        except ET.ParseError as e:
            logger.error(f"PMC XML parse error for {pmcid}: {e}")
            return None
        except Exception as e:
            logger.error(f"PMC fetch error for {pmcid}: {e}")
            return None
    
    def _parse_pmc_xml(
        self, 
        root: ET.Element, 
        pmcid_clean: str,
        include_tables: bool
    ) -> PMCArticle:
        """Parse PMC XML into structured article"""
        # Extract metadata
        article_meta = root.find(".//article-meta")
        
        title = self._extract_text(article_meta, ".//article-title") if article_meta is not None else ""
        pmid = self._extract_pmid(article_meta)
        doi = self._extract_doi(article_meta)
        journal = self._extract_text(article_meta, ".//journal-title") if article_meta is not None else ""
        year = self._extract_text(article_meta, ".//pub-date/year") if article_meta is not None else ""
        
        # Extract authors
        authors = []
        if article_meta is not None:
            for author in article_meta.findall(".//contrib[@contrib-type='author']"):
                surname = author.find(".//surname")
                given = author.find(".//given-names")
                if surname is not None:
                    author_name = "".join(surname.itertext()).strip()
                    if given is not None:
                        given_text = "".join(given.itertext()).strip()
                        if given_text:
                            author_name += f", {given_text}"
                    authors.append(author_name)
        
        # Extract full text sections
        sections = {}
        full_text_parts = []
        
        body = root.find(".//body")
        if body is not None:
            for sec in body.findall(".//sec"):
                section_title = self._extract_text(sec, "./title")
                section_text = self._extract_section_text(sec)
                
                if section_title:
                    sections[section_title] = section_text
                full_text_parts.append(section_text)
        
        full_text = "\n\n".join(full_text_parts)
        
        # Extract tables
        tables = []
        if include_tables:
            tables = self._extract_tables(root)
        
        return PMCArticle(
            pmcid=f"PMC{pmcid_clean}",
            pmid=pmid,
            title=title,
            authors=authors,
            journal=journal,
            year=year,
            full_text=full_text,
            sections=sections,
            tables=tables,
            doi=doi
        )
    
    def _extract_text(self, parent: Optional[ET.Element], xpath: str) -> str:
        """Extract text from XML element"""
        if parent is None:
            return ""
        elem = parent.find(xpath)
        return "".join(elem.itertext()).strip() if elem is not None else ""
    
    def _extract_pmid(self, article_meta: Optional[ET.Element]) -> Optional[str]:
        """Extract PMID from article metadata"""
        if article_meta is None:
            return None
        
        for id_elem in article_meta.findall(".//article-id"):
            if id_elem.get("pub-id-type") == "pmid":
                return id_elem.text
        return None
    
    def _extract_doi(self, article_meta: Optional[ET.Element]) -> Optional[str]:
        """Extract DOI from article metadata"""
        if article_meta is None:
            return None
        
        for id_elem in article_meta.findall(".//article-id"):
            if id_elem.get("pub-id-type") == "doi":
                return id_elem.text
        return None
    
    def _extract_section_text(self, sec: ET.Element) -> str:
        """Extract all paragraph text from a section"""
        paragraphs = []
        for p in sec.findall(".//p"):
            # Get all text content (including nested elements)
            text = "".join(p.itertext())
            if text.strip():
                paragraphs.append(text.strip())
        return "\n".join(paragraphs)
    
    def _extract_tables(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Extract tables from PMC XML"""
        tables = []
        
        for table_wrap in root.findall(".//table-wrap"):
            table_data = {
                "caption": "",
                "headers": [],
                "rows": []
            }
            
            # Extract caption
            caption = table_wrap.find(".//caption/p")
            if caption is not None:
                table_data["caption"] = "".join(caption.itertext()).strip()
            
            # Extract table content
            table = table_wrap.find(".//table")
            if table is not None:
                # Extract headers
                thead = table.find(".//thead")
                if thead is not None:
                    for th in thead.findall(".//th"):
                        text = "".join(th.itertext()).strip()
                        table_data["headers"].append(text)
                
                # Extract rows
                tbody = table.find(".//tbody")
                tbody_elem = tbody if tbody is not None else table
                for tr in tbody_elem.findall(".//tr"):
                    row = []
                    for td in tr.findall(".//td"):
                        text = "".join(td.itertext()).strip()
                        row.append(text)
                    if row:
                        table_data["rows"].append(row)
            
            if table_data["rows"]:
                tables.append(table_data)
        
        return tables
    
    async def _rate_limit(self):
        """Enforce rate limiting for PMC API"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        
        # Ensure at least 100ms between requests (10 req/sec max)
        min_interval = 0.1
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self._last_request_time = asyncio.get_event_loop().time()
        self._request_count += 1
