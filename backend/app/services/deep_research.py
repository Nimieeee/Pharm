"""
Deep Research Service
LangGraph-style autonomous research agent for biomedical literature review
"""

import os
import logging
import json
import httpx
import asyncio
import xml.etree.ElementTree as ET
import re
from typing import Optional, Dict, Any, List, TypedDict, AsyncGenerator
from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.pmc_fulltext import PMCFullTextService
from app.services.pdf_fulltext import PDFFullTextService
from html.parser import HTMLParser
from supabase import Client

# Initialize logger
logger = logging.getLogger(__name__)


# Shared HTML parser for DuckDuckGo results (extracted to avoid duplication)
class DDGParser(HTMLParser):
    """Parse DuckDuckGo HTML search results."""
    def __init__(self):
        super().__init__()
        self.results = []
        self.current_result = {}
        self.in_title = False
        self.in_snippet = False
    
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "a" and "result__a" in attrs_dict.get("class", ""):
            self.in_title = True
            self.current_result = {"url": attrs_dict.get("href", "")}
        elif tag == "a" and "result__snippet" in attrs_dict.get("class", ""):
            self.in_snippet = True
    
    def handle_endtag(self, tag):
        if tag == "a" and self.in_title:
            self.in_title = False
        elif tag == "a" and self.in_snippet:
            self.in_snippet = False
            if self.current_result:
                self.results.append(self.current_result)
                self.current_result = {}
    
    def handle_data(self, data):
        if self.in_title:
            self.current_result["title"] = data.strip()
        elif self.in_snippet:
            self.current_result["snippet"] = data.strip()


# ============================================================================
# STATE DEFINITION
# ============================================================================

@dataclass
class Citation:
    """Structured citation reference"""
    id: int
    title: str
    authors: str
    source: str  # "PubMed" or "Web"
    url: str
    doi: Optional[str] = None
    pmid: Optional[str] = None
    year: Optional[str] = None
    abstract: Optional[str] = None
    data_limitation: Optional[str] = None  # e.g., "Abstract Only"
    raw_apa: Optional[str] = None


@dataclass
class Finding:
    """Research finding from a source"""
    title: str
    url: str
    source: str
    study_type: Optional[str] = None  # In Silico, In Vitro, In Vivo, Clinical, Review
    key_finding: str = ""
    data_limitation: Optional[str] = None
    raw_content: str = ""
    doi: Optional[str] = None
    pmid: Optional[str] = None
    pmcid: Optional[str] = None
    _pubmed_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchStep:
    """A single research step/sub-topic"""
    id: int
    topic: str
    keywords: List[str]
    source_preference: str  # "PubMed" or "Web"
    status: str = "pending"  # pending, in_progress, completed
    findings: List[Finding] = field(default_factory=list)


@dataclass
class ResearchState:
    """The complete state of a deep research session"""
    research_question: str
    plan_overview: str = ""
    steps: List[ResearchStep] = field(default_factory=list)
    findings: List[Finding] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    report_sections: Dict[str, str] = field(default_factory=dict)
    final_report: str = ""
    iteration_count: int = 0
    max_iterations: int = 2  # Cap at 2 rounds to prevent SERP 429 loops
    status: str = "initializing"  # initializing, planning, researching, reviewing, writing, complete, error
    error_message: Optional[str] = None
    progress_log: List[str] = field(default_factory=list)


# ============================================================================
# TOOLS - PubMed and Web Search
# ============================================================================

class ResearchTools:
    """Tools for searching PubMed and the web"""
    
    def __init__(self):
        self.pubmed_base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.tavily_api_key = settings.TAVILY_API_KEY
        self.serp_api_key = settings.SERP_API_KEY
        self.serper_api_key = settings.SERPER_API_KEY
        self.semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")
        self.pubmed_api_key = os.getenv("PUBMED_API_KEY", "ba4feceadd0ef3a82d2d289e4e5738de1e09")

        if not self.pubmed_api_key:
            logger.warning("⚠️ PUBMED_API_KEY not configured. Search may be rate-limited.")

        # Lazy loading via container - avoid direct instantiation
        self._pmc_service = None
        self._pdf_service = None

    @property
    def pmc_service(self):
        """Lazy load PMC service"""
        if self._pmc_service is None:
            from app.services.pmc_fulltext import PMCFullTextService
            self._pmc_service = PMCFullTextService(api_key=self.pubmed_api_key)
        return self._pmc_service

    @property
    def pdf_service(self):
        """Lazy load PDF service"""
        if self._pdf_service is None:
            from app.services.pdf_fulltext import PDFFullTextService
            self._pdf_service = PDFFullTextService()
        return self._pdf_service

    def _extract_doi(self, text: str) -> Optional[str]:
        """Extract DOI from text or URL using regex"""
        if not text:
            return None
        # Standard DOI regex
        doi_pattern = r'10\.\d{4,9}/[-._;()/:A-Z0-9]+'
        match = re.search(doi_pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).rstrip('.')
        return None
    
    async def search_pubmed(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search PubMed using NCBI E-utilities
        Returns list of { title, abstract, pmid, doi, authors, journal, year }
        """
        results = []
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Step 1: Search for PMIDs
                search_url = f"{self.pubmed_base_url}/esearch.fcgi"
                search_params = {
                    "db": "pubmed",
                    "term": query,
                    "retmax": max_results,
                    "retmode": "json",
                    "sort": "relevance",
                    "api_key": self.pubmed_api_key
                }
                
                search_response = await client.get(search_url, params=search_params)
                search_data = search_response.json()
                
                pmids = search_data.get("esearchresult", {}).get("idlist", [])
                
                if not pmids:
                    return results
                
                # Step 2: Fetch details for each PMID
                fetch_url = f"{self.pubmed_base_url}/efetch.fcgi"
                fetch_params = {
                    "db": "pubmed",
                    "id": ",".join(pmids),
                    "retmode": "xml",
                    "api_key": self.pubmed_api_key
                }
                
                fetch_response = await client.get(fetch_url, params=fetch_params)
                
                # Parse XML response
                root = ET.fromstring(fetch_response.text)
                
                for article in root.findall(".//PubmedArticle"):
                    try:
                        medline = article.find(".//MedlineCitation")
                        article_data = medline.find(".//Article") if medline is not None else None
                        
                        if article_data is None:
                            continue
                        
                        # Extract PMID
                        pmid_elem = medline.find(".//PMID")
                        pmid = pmid_elem.text if pmid_elem is not None else ""
                        
                        # Extract title (for display in findings)
                        title_elem = article_data.find(".//ArticleTitle")
                        title = title_elem.text if title_elem is not None else "No title"
                        
                        # Extract abstract
                        abstract_elem = article_data.find(".//Abstract/AbstractText")
                        abstract = abstract_elem.text if abstract_elem is not None else ""
                        
                        # Extract DOI and PMCID
                        doi = ""
                        pmcid = ""
                        for id_elem in article.findall(".//ArticleIdList/ArticleId"): # Corrected path to ArticleId
                            id_type = id_elem.get("IdType")
                            if id_type == "doi":
                                doi = id_elem.text
                            elif id_type == "pmc":
                                pmcid = id_elem.text
                                
                        # Extract authors manually. We use the custom format: LastName, I., LastName, I.
                        authors_list = []
                        for author in article_data.findall(".//AuthorList/Author"): # Corrected path to Author
                            last_name_node = author.find("LastName")
                            initials_node = author.find("Initials")
                            
                            if last_name_node is not None:
                                last_name = last_name_node.text or ""
                                initials = initials_node.text or "" if initials_node is not None else ""
                                
                                if initials:
                                    formatted_initials = ".".join(list(initials)) + "."
                                    authors_list.append(f"{last_name}, {formatted_initials}")
                                else:
                                    authors_list.append(last_name)
                        
                        # The user requested NO truncation (e.g. no "et al."). Join all extracted authors.
                        author_str = ", ".join(authors_list)
                        
                        # Extract journal
                        journal_elem = article_data.find(".//Journal/Title")
                        journal = journal_elem.text if journal_elem is not None else ""
                        
                        # Extract year
                        year_elem = article_data.find(".//Journal/JournalIssue/PubDate/Year")
                        year = year_elem.text if year_elem is not None else ""
                        
                        # Build full APA-style citation
                        apa_citation = f"{author_str} ({year or 'n.d.'}). {title}. {journal}."
                        if doi:
                            apa_citation += f" doi:{doi}"
                        
                        result_item = {
                            "title": title,
                            "abstract": abstract or "[Abstract not available]",
                            "pmid": pmid,
                            "pmcid": pmcid, # Added pmcid
                            "doi": doi,
                            "authors": author_str,
                            "journal": journal,
                            "year": year,
                            "apa_citation": apa_citation,
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                        }
                        
                        results.append(result_item)
                        
                    except Exception as e:
                        # Log specific parsing errors but continue
                        logger.warning(f"Error parsing PubMed article {pmid if 'pmid' in locals() else 'unknown'}: {e}")
                        continue
                        
        except httpx.TimeoutException:
            logger.warning("PubMed search timed out. Please try again later.")
            # Return partial results if we have them, or empty list
            
        except httpx.HTTPError as e:
            logger.error(f"PubMed API connection error: {e}")
            
        except Exception as e:
            logger.error(f"PubMed search error: {str(e)}")
        
        return results

    async def search_semantic_scholar(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search Semantic Scholar API for comprehensive academic papers.
        Returns list of { title, abstract, doi, authors, venue, year, citationCount, url, openAccessPdf }
        """
        results = []
        search_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,authors,year,abstract,citationCount,externalIds,venue,url,openAccessPdf"
        }
        
        headers = {}
        if self.semantic_scholar_api_key:
            headers["x-api-key"] = self.semantic_scholar_api_key
            
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.get(search_url, params=params, headers=headers)
                
                if response.status_code == 429:
                    logger.error("Semantic Scholar API Rate Limit (429) reached.")
                    return results
                    
                if response.status_code == 200:
                    data = response.json()
                    
                    for paper in data.get('data', []):
                        if not paper:
                            continue
                            
                        # Extract basic fields
                        title = paper.get('title', "No title")
                        abstract = paper.get('abstract', "")
                        if not abstract: # Skip papers without abstracts for deep research
                            continue
                            
                        year = str(paper.get('year', ""))
                        venue = paper.get('venue', "")
                        citation_count = paper.get('citationCount', 0)
                        
                        # Extract external IDs
                        external_ids = paper.get('externalIds', {})
                        doi = external_ids.get('DOI', "")
                        pmid = external_ids.get('PubMed', "")
                        
                        # Extract URL
                        url = paper.get('url', "")
                        if not url and doi:
                            url = f"https://doi.org/{doi}"
                            
                        # Format authors natively
                        authors_list = []
                        for author in paper.get('authors', []):
                            name = author.get('name', '')
                            if name:
                                # Semantic Scholar typically returns "First Last". 
                                # We want to try splitting to format as "Last, F."
                                parts = name.split()
                                if len(parts) >= 2:
                                    last_name = parts[-1]
                                    first_initial = parts[0][0] + "."
                                    authors_list.append(f"{last_name}, {first_initial}")
                                else:
                                    authors_list.append(name)
                        
                        author_str = ", ".join(authors_list)
                        if not author_str:
                            author_str = "Unknown"
                            
                        result_item = {
                            "title": title,
                            "abstract": abstract,
                            "doi": doi,
                            "pmid": pmid,
                            "authors": author_str,
                            "journal": venue,
                            "year": year,
                            "citationCount": citation_count,
                            "url": url
                        }
                        results.append(result_item)
                        
        except httpx.TimeoutException:
            logger.warning("Semantic Scholar search timed out.")
        except httpx.HTTPError as e:
            logger.error(f"Semantic Scholar API connection error: {e}")
        except Exception as e:
            logger.error(f"Semantic Scholar search error: {e}")
            
        return results
    
    async def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using DuckDuckGo only (Tavily removed per user request)
        Returns list of { title, snippet, url }
        """
        results = []
        
        # Use DuckDuckGo HTML search (no API key needed)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": f"{query} site:nih.gov OR site:fda.gov OR site:pubmed.ncbi.nlm.nih.gov"},
                    headers={"User-Agent": "Mozilla/5.0 (compatible; Benchside/1.0)"}
                )
                
                # Parse DuckDuckGo HTML results
                parser = DDGParser()
                parser.feed(response.text)
                results = parser.results[:max_results]
                
        except Exception as e:
            logger.error(f"Web search error: {e}")
        
        return results
    
    async def search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search DuckDuckGo (HTML fallback)
        Returns list of { title, snippet, url }
        """
        results = []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": query},
                    headers={"User-Agent": "Mozilla/5.0 (compatible; Benchside/1.0)"}
                )
                
                if response.status_code == 200:
                    parser = DDGParser()
                    parser.feed(response.text)
                    
                    # Format results to match other tools
                    for r in parser.results[:max_results]:
                        results.append({
                            "title": r.get("title", ""),
                            "snippet": r.get("snippet", ""),
                            "url": r.get("url", ""),
                            "source": "DuckDuckGo"
                        })
                        
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")
            
        return results
    
    async def search_google_scholar(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search Google Scholar using SERP API
        Returns list of academic papers with citations, authors, and links
        
        Args:
            query: Search query
            max_results: Max results (default 10)
            
        Returns:
            List of { title, snippet, authors, year, cited_by, url, pdf_url }
        """
        results = []
        
        if not self.serp_api_key:
            logger.warning("SERP_API_KEY not configured, skipping Google Scholar search")
            return results
        
        # Fast-fail if SERP API was already rate-limited this session
        if getattr(self, '_serp_disabled', False):
            return results
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "engine": "google_scholar",
                        "q": query,
                        "api_key": self.serp_api_key,
                        "num": min(max_results, 20),  # SERP API max is 20
                        "hl": "en"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    organic_results = data.get("organic_results", [])
                    
                    for result in organic_results:
                        # Extract publication info
                        publication_info = result.get("publication_info", {})
                        
                        # Parse authors (remove truncation logic to list all authors up to 20 as requested)
                        authors_list = publication_info.get("authors", [])
                        authors_names = [a.get("name", "") for a in authors_list]
                        if len(authors_names) > 20: # Cap at 20 max to avoid absurdly long lists
                            authors = ", ".join(authors_names[:19]) + ", et al."
                        else:
                            authors = ", ".join(authors_names)
                        
                        # Parse Journal and Year from summary
                        # Format: "Authors - Journal, Year - Publisher"
                        summary = publication_info.get("summary", "")
                        journal = ""
                        year = ""
                        
                        if summary:
                            parts = summary.split(" - ")
                            if len(parts) >= 2:
                                # Middle part usually contains "Journal, Year"
                                # e.g. "New England Journal of Medicine, 1993"
                                journal_year = parts[1]
                                jy_parts = journal_year.split(",")
                                if len(jy_parts) >= 2:
                                    year = jy_parts[-1].strip()
                                    journal = ",".join(jy_parts[:-1]).strip()
                                else:
                                    # Sometimes just year or just journal
                                    if journal_year.strip().isdigit():
                                        year = journal_year.strip()
                                    else:
                                        journal = journal_year.strip()
                        
                        # Get citation count
                        inline_links = result.get("inline_links", {})
                        cited_by = inline_links.get("cited_by", {})
                        citation_count = cited_by.get("total", 0)
                        
                        # Get PDF link if available
                        resources = result.get("resources", [])
                        pdf_url = next((r.get("link") for r in resources if r.get("file_format") == "PDF"), "")
                        
                        results.append({
                            "title": result.get("title", ""),
                            "snippet": result.get("snippet", ""),
                            "authors": authors,
                            "year": year,
                            "journal": journal,
                            "cited_by": citation_count,
                            "url": result.get("link", ""),
                            "pdf_url": pdf_url,
                            "source": "Google Scholar",
                            "doi": self._extract_doi(result.get("link", "") + " " + result.get("snippet", ""))
                        })
                    
                    return results[:max_results]
                else:
                    logger.warning(f"SERP API error: {response.status_code}")
                    if response.status_code == 429:
                        self._serp_disabled = True
                        logger.warning("SERP API rate-limited (429). Disabling for this session.")
                    
        except Exception as e:
            logger.warning(f"Google Scholar search error: {e}")
        
        return results

    async def search_serper(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search using Serper.dev API
        """
        results = []
        if not self.serper_api_key:
            return results
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={
                        "X-API-KEY": self.serper_api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "num": max_results
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get("organic", []):
                        results.append({
                            "title": result.get("title", ""),
                            "snippet": result.get("snippet", ""),
                            "url": result.get("link", ""),
                            "source": "Serper"
                        })
        except Exception as e:
            logger.warning(f"Serper search error: {e}")
        return results


# ============================================================================
# DEEP RESEARCH SERVICE
# ============================================================================

class DeepResearchService:
    """
    Autonomous research agent using LangGraph-style workflow
    Nodes: Planner → Researcher → Reviewer → Writer
    
    Uses ServiceContainer for dependencies where possible.
    """

    def __init__(self, db: Client):
        self.db = db
        self.tools = ResearchTools()
        self.mistral_api_key = settings.MISTRAL_API_KEY
        self.mistral_base_url = "https://api.mistral.ai/v1"
        self._container = None
    
    @property
    def container(self):
        """Lazy load container for accessing other services"""
        if self._container is None:
            from app.core.container import container
            self._container = container.initialize(self.db)
        return self._container

    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        json_mode: bool = False,
        max_tokens: int = 8192,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        mode: str = "deep_research",
    ) -> str:
        """
        Call LLM via multi-provider routing with automatic fallback.
        Uses specified mode for optimal model selection.
        """
        from app.services.multi_provider import get_multi_provider

        try:
            logger.info(f"🔬 Deep Research LLM: Calling multi-provider (json={json_mode}, tokens={max_tokens})")

            mp = get_multi_provider()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # Use a slightly higher temperature for planning if not json_mode
            temp = 0.3 if json_mode else 0.7

            start_time = time.time()
            response = await mp.generate(
                messages=messages,
                mode=mode,
                max_tokens=max_tokens,
                temperature=temp,
                json_mode=json_mode,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
            )
            
            if not response:
                raise ValueError("Empty content from LLM")
            
            # Strip Qwen 3.5 thinking mode tags (<think>...</think>)
            # The model generates internal reasoning before the final answer
            if '<think>' in response:
                # Extract only the content after </think>
                think_end = response.rfind('</think>')
                if think_end != -1:
                    response = response[think_end + len('</think>'):].strip()
                    logger.info(f"🧠 Stripped thinking tags from response")
            
            duration = time.time() - start_time
            
            logger.info(f"✅ Deep Research LLM: Received response ({len(response)} chars, {duration:.2f}s)")
            return response
            
        except Exception as e:
            logger.error(f"❌ CRITICAL: Deep Research LLM failed: {e}")
            # Return a valid JSON error structure if json_mode was requested, to prevent downstream crash
            if json_mode:
                return '{"error": "Model failure", "plan_overview": "Research failed", "steps": []}'
            return "Deep Research unavailable at this time."

    def _is_valid_finding(self, finding: Finding) -> bool:
        """
        Validate if a finding is high quality enough to be used.
        Filters out empty results, scraper blocks, and malformed data.
        """
        # 1. Check for missing essential fields
        if not finding.title or len(finding.title) < 5:
            return False
        if not finding.url or not finding.url.startswith("http"):
            return False
        if not finding.raw_content or len(finding.raw_content) < 20:
            return False
            
        # 2. Check for "garbage" titles (scraper blocks)
        garbage_terms = [
            "access denied", "captcha", "robot check", "403 forbidden", 
            "404 not found", "page not found", "just a moment", 
            "enable javascript", "security check", "challenge validation"
        ]
        if any(term in finding.title.lower() for term in garbage_terms):
            return False
            
        return True

    # ========================================================================
    # NODE A: THE PLANNER (Deconstructor)
    # ========================================================================
    
    async def _node_planner(self, state: ResearchState) -> ResearchState:
        """
        Break down the research question into sub-topics using PICO/MoA framework
        """
        state.status = "planning"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Starting research planning...")
        
        state.progress_log.append(f"[{datetime.now().isoformat()}] Analyzing research topic: {state.research_question}")
        
        system_prompt = """You are a Principal Investigator with expertise in systematic biomedical research reviews.

YOUR TASK: Analyze the research question and create an intelligent, structured research plan.

STEP 1 - IDENTIFY THE RESEARCH DOMAIN:
Carefully analyze the question to determine its primary focus:

1. **Drug/Treatment Research**
   → Mechanism of action, Pharmacokinetics/dynamics, Clinical efficacy, Adverse effects, Drug interactions, Guidelines

2. **Animal Model Research**
   → Model characteristics & physiology, Genetic manipulation methods, Disease modeling applications, 
   → Experimental protocols, Validation & limitations, Comparative analysis with human disease

3. **Disease/Pathology Research**
   → Molecular etiology, Pathophysiological mechanisms, Clinical manifestations, Diagnostic approaches,
   → Current treatments, Emerging therapies, Biomarkers

4. **Laboratory Technique/Method**
   → Underlying scientific principles, Step-by-step protocol, Applications & use cases,
   → Troubleshooting & optimization, Advantages vs limitations, Comparison with alternatives

5. **Molecular/Cellular Mechanism**
   → Signaling pathways, Molecular interactions, Regulatory networks, Cellular responses,
   → Disease relevance, Therapeutic targeting opportunities

6. **Clinical Trial/Study Analysis**
   → Study design & methodology, Patient population, Primary/secondary endpoints,
   → Results & statistical analysis, Clinical implications, Limitations

7. **Pharmacogenomics/Precision Medicine**
   → Genetic variants, Gene-drug interactions, Biomarker identification, Clinical implementation,
   → Personalized dosing, Ethical considerations

8. **Toxicology/Safety Assessment**
   → Toxicological mechanisms, Dose-response relationships, Target organ toxicity,
   → Risk assessment, Regulatory considerations, Mitigation strategies

STEP 2 - CREATE STRATEGIC SUB-TOPICS (6 to 10):
Based on the identified domain and the complexity of the research question, break down the question into 6 to 10 complementary sub-topics. If the question is simple, use 6 topics. If it is highly complex or multi-faceted, expand up to 10 topics.
Each sub-topic must:
- Be specific and actionable (not vague)
- Use precise scientific terminology
- Cover a distinct aspect (no overlap)
- Include 3-5 relevant keywords for searching

STEP 3 - DEFINE SEARCH STREAMS:
Instead of random queries, group your steps into 3-4 logical "Streams":
1. **Mechanistic Stream**: Molecular pathways, sensors, and biochemical interactions.
2. **Clinical Stream**: Trial phases, NCT IDs, human safety data, and efficacy metrics.
3. **Comparative/landscape Stream**: Benchmarking vs standard-of-care (SOC).
4. **Synthesis/Gap Stream**: Evidence voids and future research suggestions.

STEP 4 - INTERNAL CLARIFICATION:
In the 'plan_overview', you MUST explicitly state the Assumed Focus (e.g., "Assuming a 5-year recency priority and all cancer stages unless specified").

RETURN FORMAT (strict JSON):
RETURN FORMAT (strict JSON):
{
"plan_overview": "3-4 sentences describing: (1) assumed focus/timeframe, (2) search streams structure, (3) target evidence density",
"steps": [
        {
            "id": 1,
            "topic": "Highly specific sub-topic covering aspect 1",
            "keywords": ["precise_term_1", "precise_term_2", "precise_term_3", "additional_term"],
            "source_preference": "PubMed"
        },
        {
            "id": 2,
            "topic": "Highly specific sub-topic covering aspect 2",
            "keywords": ["precise_term_1", "precise_term_2", "precise_term_3"],
            "source_preference": "PubMed"
        },
        {
            "id": 3,
            "topic": "Highly specific sub-topic covering aspect 3",
            "keywords": ["precise_term_1", "precise_term_2", "precise_term_3"],
            "source_preference": "Web"
        },
        {
            "id": 4,
            "topic": "Highly specific sub-topic covering aspect 4",
            "keywords": ["precise_term_1", "precise_term_2", "precise_term_3"],
            "source_preference": "PubMed"
        },
        {
            "id": 5,
            "topic": "Highly specific sub-topic covering aspect 5",
            "keywords": ["precise_term_1", "precise_term_2", "precise_term_3"],
            "source_preference": "PubMed"
        },
        {
            "id": 6,
            "topic": "Highly specific sub-topic covering aspect 6",
            "keywords": ["precise_term_1", "precise_term_2", "precise_term_3"],
            "source_preference": "Web"
        }
        // ... include up to 10 topics if the complexity warrants it
    ]
}

QUALITY EXAMPLES:

Example 1: "Zebrafish as a pharmacological screening model"
Domain: Animal Model Research
{
    "plan_overview": "This is an animal model research question. Strategy: Examine zebrafish model validation, genetic toolkits, high-throughput screening applications, and comparative advantages. Expected: Comprehensive analysis of zebrafish utility in drug discovery.",
    "steps": [
        {"id": 1, "topic": "Zebrafish genetics and transgenic model development for target validation", "keywords": ["zebrafish", "transgenic", "CRISPR", "genetic tools", "model validation"], "source_preference": "PubMed"},
        {"id": 2, "topic": "High-throughput phenotypic screening protocols in zebrafish embryos", "keywords": ["zebrafish", "high-throughput screening", "phenotypic assay", "drug discovery"], "source_preference": "PubMed"},
        {"id": 3, "topic": "Current FDA-approved drugs discovered using zebrafish models", "keywords": ["zebrafish", "drug discovery", "FDA approval", "case studies"], "source_preference": "Web"},
        {"id": 4, "topic": "Comparative physiology: zebrafish versus mammalian models in pharmacology", "keywords": ["zebrafish", "comparative pharmacology", "translational research", "mammalian models"], "source_preference": "PubMed"}
    ]
}

Example 2: "CRISPR-Cas9 off-target effects in therapeutic applications"
Domain: Laboratory Technique + Clinical Safety
{
    "plan_overview": "This combines laboratory technique and safety assessment. Strategy: Investigate molecular mechanisms of off-target effects, detection methods, mitigation strategies, and clinical trial outcomes. Expected: Balanced analysis of risks and current solutions.",
    "steps": [
        {"id": 1, "topic": "Molecular mechanisms of CRISPR-Cas9 off-target DNA cleavage", "keywords": ["CRISPR-Cas9", "off-target effects", "DNA cleavage", "molecular mechanism"], "source_preference": "PubMed"},
        {"id": 2, "topic": "Whole-genome sequencing methods for detecting CRISPR off-target mutations", "keywords": ["CRISPR", "off-target detection", "whole genome sequencing", "validation"], "source_preference": "PubMed"},
        {"id": 3, "topic": "High-fidelity Cas9 variants and guide RNA design strategies to minimize off-targets", "keywords": ["high-fidelity Cas9", "guide RNA design", "specificity", "off-target reduction"], "source_preference": "PubMed"},
        {"id": 4, "topic": "Clinical trial safety data for CRISPR-based therapies: reported adverse events", "keywords": ["CRISPR clinical trials", "adverse events", "safety", "gene therapy"], "source_preference": "Web"}
    ]
}

Example 3: "mTOR signaling pathway in autophagy regulation"
Domain: Molecular Mechanism
{
    "plan_overview": "This is a molecular mechanism question. Strategy: Map mTOR pathway components, autophagy regulation mechanisms, disease implications, and therapeutic modulation. Expected: Detailed mechanistic framework.",
    "steps": [
        {"id": 1, "topic": "mTORC1 and mTORC2 complex composition, upstream activators and downstream effectors", "keywords": ["mTOR", "mTORC1", "mTORC2", "signaling pathway", "regulation"], "source_preference": "PubMed"},
        {"id": 2, "topic": "Molecular mechanisms by which mTOR inhibits autophagy initiation via ULK1 phosphorylation", "keywords": ["mTOR", "autophagy", "ULK1", "phosphorylation", "regulation"], "source_preference": "PubMed"},
        {"id": 3, "topic": "Disease states involving dysregulated mTOR-autophagy axis: cancer, neurodegeneration, aging", "keywords": ["mTOR", "autophagy", "disease", "cancer", "neurodegeneration"], "source_preference": "PubMed"},
        {"id": 4, "topic": "Pharmacological mTOR inhibitors (rapamycin, rapalogs) and autophagy modulation in clinical use", "keywords": ["mTOR inhibitors", "rapamycin", "autophagy", "therapeutics", "clinical trials"], "source_preference": "Web"}
    ]
}

NOW ANALYZE THE USER'S QUESTION AND CREATE THE RESEARCH PLAN.
"""
        
        response = await self._call_llm(system_prompt, f"Research Topic: {state.research_question}", json_mode=True)
        
        try:
            plan = json.loads(response)
            state.plan_overview = plan.get("plan_overview", "")
            
            for step_data in plan.get("steps", []):
                step = ResearchStep(
                    id=step_data.get("id"),
                    topic=step_data.get("topic"),
                    keywords=step_data.get("keywords", []),
                    source_preference=step_data.get("source_preference", "PubMed")
                )
                state.steps.append(step)
                
            state.progress_log.append(f"[{datetime.now().isoformat()}] Plan created with {len(state.steps)} steps")
            
        except json.JSONDecodeError:
            state.error_message = "Failed to generate research plan"
            state.status = "error"
            
        return state

    async def _node_researcher(self, state: ResearchState) -> ResearchState:
        """
        Execute searches for each sub-topic using PubMed AND Web tools in parallel.

        PERFORMANCE MONITORING: Logs timing for each search operation
        """
        state.status = "researching"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Starting multi-source literature search...")

        logger.info("⏱️ [PERF MONITOR] Researcher Phase Started")
        phase_start = datetime.now()

        for step in state.steps:
            if step.status == "completed":
                continue

            step.status = "in_progress"
            step_start = datetime.now()
            state.progress_log.append(f"[{datetime.now().isoformat()}] Researching: {step.topic}")
            logger.info(f"⏱️ [PERF] Step '{step.topic[:50]}...' started")
            
            # Generate optimized search queries
            query_prompt = f"""Convert this research topic into effective search queries:
Topic: {step.topic}
Keywords: {', '.join(step.keywords)}

Generate 3 search queries.
Return as JSON: {{"queries": ["query1", "query2", "query3"]}}"""

            query_response = await self._call_llm(
                "You are a search specialist. Generate precise biomedical search queries.",
                query_prompt,
                json_mode=True
            )
            
            try:
                queries_data = json.loads(query_response)
                queries = queries_data.get("queries", [" ".join(step.keywords)])
            except Exception:
                queries = [" ".join(step.keywords)]
            
            # Execute searches
            step_findings_count = 0
            query_times = []

            for query in queries:
                query_start = datetime.now()

                # Parallel Search: Semantic Scholar, PubMed, Web (Tavily), DuckDuckGo, Serper
                # Keeping 50 PubMed + 50 Web results per sub-topic for comprehensive coverage
                tasks = [
                    self.tools.search_semantic_scholar(query, max_results=20),
                    self.tools.search_pubmed(query, max_results=50),  # Keep 50 for comprehensive coverage
                    self.tools.search_web(query, max_results=5),
                    self.tools.search_duckduckgo(query, max_results=5),
                    self.tools.search_serper(query, max_results=5)
                ]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                query_time = (datetime.now() - query_start).total_seconds()
                query_times.append(query_time)
                logger.info(f"⏱️ [PERF] Query '{query[:40]}...' took {query_time:.2f}s")
                
                results_s2 = results[0] if not isinstance(results[0], Exception) else []
                results_pubmed = results[1] if not isinstance(results[1], Exception) else []
                results_web = results[2] if not isinstance(results[2], Exception) else []
                results_ddg = results[3] if not isinstance(results[3], Exception) else []
                results_serper = results[4] if not isinstance(results[4], Exception) else []
                
                # Process Semantic Scholar Results
                for r in results_s2:
                    raw_content = r.get("abstract", "")
                    data_limitation = "Abstract Only"
                    
                    # Check for Open Access PDF
                    oa_pdf = r.get("open_access_pdf")
                    if oa_pdf and isinstance(oa_pdf, dict) and oa_pdf.get("url"):
                        pdf_url = oa_pdf.get("url")
                        paper_id = r.get("uuid")
                        title = r.get("title")
                        
                        # Fetch full text
                        pdf_article = await self.tools.pdf_service.fetch_and_extract(pdf_url, paper_id, title)
                        if pdf_article and pdf_article.full_text:
                            raw_content = pdf_article.full_text
                            data_limitation = None
                            state.progress_log.append(f"[{datetime.now().isoformat()}] Fetched SS PDF for {paper_id}")
                            
                    finding = Finding(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        source="Semantic Scholar",
                        raw_content=raw_content,
                        data_limitation=data_limitation,
                        doi=r.get("doi", ""),
                        pmid=r.get("pmid", "")
                    )
                    # Store rich metadata for citation formatting and fallback sorting
                    finding._pubmed_data = {
                        "authors": r.get("authors", ""),
                        "year": r.get("year", ""),
                        "journal": r.get("journal", ""),
                        "doi": r.get("doi", ""),
                        "pmid": r.get("pmid", ""),
                        "citationCount": r.get("citationCount", 0)
                    }
                    if self._is_valid_finding(finding):
                        step.findings.append(finding)
                        state.findings.append(finding)
                        step_findings_count += 1
                        
                # Process PubMed Results
                for r in results_pubmed:
                    pmcid = r.get("pmcid")
                    full_text = ""
                    data_limitation = "Abstract Only"
                    
                    if pmcid:
                        # Fetch full text from PMC
                        pmc_article = await self.tools.pmc_service.fetch_fulltext(pmcid)
                        if pmc_article and pmc_article.full_text:
                            full_text = pmc_article.full_text
                            data_limitation = None
                            state.progress_log.append(f"[{datetime.now().isoformat()}] Fetched PMC full-text for {pmcid}")
                            
                    raw_content = full_text if full_text else r.get("abstract", "")
                    
                    finding = Finding(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        source="PubMed",
                        raw_content=raw_content,
                        data_limitation=data_limitation,
                        doi=r.get("doi", ""),
                        pmid=r.get("pmid", ""),
                        pmcid=pmcid
                    )
                    finding._pubmed_data = {
                        "authors": r.get("authors", ""),
                        "year": r.get("year", ""),
                        "journal": r.get("journal", ""),
                        "doi": r.get("doi", ""),
                        "pmid": r.get("pmid", ""),
                        "pmcid": pmcid,
                        "apa": r.get("apa_citation", "")
                    }
                    if self._is_valid_finding(finding):
                        step.findings.append(finding)
                        state.findings.append(finding)
                        step_findings_count += 1
                
                # Process Web Results (Tavily)
                for r in results_web:
                    finding = Finding(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        source="Web",
                        raw_content=r.get("snippet", ""),
                        doi=r.get("doi")
                    )
                    if self._is_valid_finding(finding):
                        step.findings.append(finding)
                        state.findings.append(finding)
                        step_findings_count += 1

                # Process DuckDuckGo Results
                for r in results_ddg:
                    finding = Finding(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        source="DuckDuckGo",
                        raw_content=r.get("snippet", "")
                    )
                    if self._is_valid_finding(finding):
                        step.findings.append(finding)
                        state.findings.append(finding)
                        step_findings_count += 1

                # Google Scholar logic previously removed, skip directly to Serper

                # Process Serper Results
                for r in results_serper:
                    finding = Finding(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        source="Serper",
                        raw_content=r.get("snippet", "")
                    )
                    if self._is_valid_finding(finding):
                        step.findings.append(finding)
                        state.findings.append(finding)
                        step_findings_count += 1
            
            step.status = "completed"
            step_time = (datetime.now() - step_start).total_seconds()
            avg_query_time = sum(query_times) / len(query_times) if query_times else 0

            state.progress_log.append(f"[{datetime.now().isoformat()}] Found {step_findings_count} sources for: {step.topic}")

            # PERFORMANCE MONITORING: Log step timing
            logger.info(f"⏱️ [PERF] Step completed in {step_time:.2f}s (avg query: {avg_query_time:.2f}s, found {step_findings_count} sources)")

        # PERFORMANCE MONITORING: Log phase summary
        phase_time = (datetime.now() - phase_start).total_seconds()
        total_queries = sum(len(q) for q in [step.keywords + [step.topic] for step in state.steps])
        logger.info(f"⏱️ [PERF MONITOR] Researcher Phase Summary:")
        logger.info(f"  - Total time: {phase_time:.2f}s")
        logger.info(f"  - Steps processed: {len(state.steps)}")
        logger.info(f"  - Total queries: {len(query_times)}")
        logger.info(f"  - Total findings: {len(state.findings)}")
        logger.info(f"  - Avg time per query: {(phase_time / len(query_times)):.2f}s" if query_times else "  - No queries executed")
        logger.info(f"  - Findings per second: {(len(state.findings) / phase_time):.2f}" if phase_time > 0 else "  - N/A")
        
        state.iteration_count += 1
        
        # Heuristic quality check
        if len(state.findings) < 5:
            logger.error(f"⚠️ CRITICAL RESEARCH FAILURE: Only {len(state.findings)} sources found. Deep Research will likely be low quality.")
            state.progress_log.append(f"[{datetime.now().isoformat()}] WARNING: Minimal search results found. Report depth may be affected.")
            
        logger.info(f"Researcher node finished with {len(state.findings)} findings.")
        if len(state.findings) < 5:
            logger.warning("Researcher node produced fewer than 5 findings - search tools may have failed silently")
        return state
    
    async def _node_reviewer(self, state: ResearchState) -> ResearchState:
        """
        Review findings and decide if more research is needed (Recursive Loop).
        """
        state.status = "reviewing"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Reviewing {len(state.findings)} findings...")
        
        if not state.findings:
            state.progress_log.append(f"[{datetime.now().isoformat()}] Warning: No findings to review.")
            return state
        
        # Prepare findings for review
        findings_text = ""
        for i, f in enumerate(state.findings[-100:]):  # Review last 100 findings
            findings_text += f"\n[{i+1}] Title: {f.title}\nSource: {f.source}\nContent: {f.raw_content[:300]}...\n"
        
        # Check for sufficiency
        system_prompt = (
            "You are a Senior Editor (AI). Analyze the gathered research.\n"
            "Is it sufficient to write a comprehensive, academic-grade report on the user's topic?\n"
            "If 'YES', proceed.\n"
            "If 'NO', generate 2 new specific search queries to fill the gaps.\n\n"
            "Return JSON:\n"
            "{\n"
            '    "sufficient": boolean,\n'
            '    "missing_info": "Description of what is missing",\n'
            '    "new_queries": ["query1", "query2"] (only if sufficient is false)\n'
            "}\n\n"
            "CRITERIA FOR SUFFICIENCY:\n"
            "1. At least 15 unique, high-quality citations found.\n"
            "2. All core aspects of the research question covered.\n"
            "3. If <10 citations found, sufficient MUST be false."
        )

        user_prompt = f"Research Question: {state.research_question}\n\nFindings Summary:\n{findings_text}"
        
        response = await self._call_llm(system_prompt, user_prompt, json_mode=True)
        
        review = {"sufficient": True, "missing_info": "", "new_queries": []}
        try:
            # Strip markdown if present
            clean_response = response.replace('```json', '').replace('```', '').strip()
            review = json.loads(clean_response)
        except Exception as e:
            state.progress_log.append(f"[{datetime.now().isoformat()}] Review parsing error: {e}. Defaulting to sufficient.")
            
        # ALWAYS build citations from findings, regardless of sufficiency/recursion
        citation_id = 1
        for f in state.findings:
            # Deduplicate based on title (case-insensitive)
            f_title_norm = f.title.lower().strip()
            if not any(c.title.lower().strip() == f_title_norm for c in state.citations):
                pubmed_data = getattr(f, '_pubmed_data', None)
                citation = Citation(
                    id=citation_id,
                    title=f.title,
                    authors=pubmed_data.get("authors", "") if pubmed_data else "",
                    source=pubmed_data.get("journal", f.source) if pubmed_data else f.source,
                    url=f.url,
                    doi=pubmed_data.get("doi", "") if pubmed_data else None,
                    pmid=pubmed_data.get("pmid", "") if pubmed_data else None,
                    year=pubmed_data.get("year", "") if pubmed_data else None,
                    data_limitation=f.data_limitation,
                    raw_apa=pubmed_data.get("apa", "") if pubmed_data else None
                )
                state.citations.append(citation)
                citation_id += 1
        
        # Now handle the recursion logic
        if not review.get("sufficient", True) and state.iteration_count < state.max_iterations:
            state.progress_log.append(f"[{datetime.now().isoformat()}] Gaps detected: {review.get('missing_info', 'Unknown gaps')}. Recursion triggered.")
            
            # Add new steps for recursion
            new_queries = review.get("new_queries", [])[:1]  # Cap at 1 gap-fill query to avoid SERP overload
            for i, query in enumerate(new_queries):
                new_step = ResearchStep(
                    id=len(state.steps) + 1,
                    topic=f"Gap Fill: {query}",
                    keywords=query.split(),
                    source_preference="Web" # Default to web for gap filling
                )
                state.steps.append(new_step)
            
            # Reset status to trigger researcher again
            await self._node_researcher(state)
        else:
            state.progress_log.append(f"[{datetime.now().isoformat()}] Research sufficient. Proceeding to writing.")
        
        logger.info(f"Reviewer node successfully built {len(state.citations)} citations.")
        return state

    # ========================================================================
    # NODE D: THE WRITER (Medical Writer)
    # ========================================================================
    
    async def _node_writer(self, state: ResearchState) -> ResearchState:
        """
        Synthesize findings into a professional research report.
        """
        state.status = "writing"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Drafting final manuscript...")
        logger.info(f"ENTERING WRITER NODE WITH: {len(state.findings)} findings, {len(state.citations)} citations")
        
        # Handle empty results
        if not state.citations and not state.findings:
            state.final_report = f"# Research Report: {state.research_question}\n\nNo significant data found."
            state.status = "complete"
            return state

        # Prepare validated findings
        # --- Context Relevance Check ---
        # NOTE: Bypassed aggressive LLM filtering here because it was falsely returning 0 IDs 
        # and wiping the citation list under Mistral/Groq. 
        # The researcher node already filters heuristics.
        
        # Compute citationCounts for sorting (Tier 2 fallback needs Top 20)
        for citation in state.citations:
            finding = next((f for f in state.findings if f.title == citation.title), None)
            if finding and hasattr(finding, '_pubmed_data'):
                citation._citationCount = finding._pubmed_data.get("citationCount", 0)
            else:
                citation._citationCount = 0
                
        # Sort citations by relevance (citationCount descending)
        sorted_citations = sorted(state.citations, key=lambda c: getattr(c, "_citationCount", 0), reverse=True)

        def build_findings_text(citations_list):
            text = ""
            for c in citations_list:
                f = next((f_ for f_ in state.findings if f_.title == c.title), None)
                if f:
                    text += f"\n[{c.id}] {c.title}\n"
                    text += f"   Authors: {c.authors or 'Unknown'}\n"
                    text += f"   Source: {c.source} | Year: {c.year or 'n.d.'}\n"
                    if c.doi:
                        text += f"   DOI: {c.doi}\n"
                    if c.pmid:
                        text += f"   PMID: {c.pmid}\n"
                    text += f"   Key Content: {f.raw_content[:4000]}\n"
            return text

        report_sys_prompt = f"""You are a senior medical/scientific research analyst.
Your task is to write a comprehensive, highly academic review article.
Target length: **2,500–3,000 words** of dense, substantive analysis.
The tone must be objective, empirical, and strictly scientific.

## DEPTH OVER BREADTH:
You have access to many sources but DO NOT spread thin. Select the 15-25 MOST relevant papers and
analyze them IN DEPTH with specific data points, methodology details, and quantitative results.
A deeply analyzed subset is far more valuable than a shallow mention of every source.

## GOLD STANDARD BENCHMARKS:
To match high-impact journals (e.g., Nature, Lancet, Cell), you MUST:
1. **Demand Quantitative Density**: Never say "more effective" or "showed promise." Say "increased ORR by 32%% (p < 0.05)" or "demonstrated IC50 of 0.12 μM in A549 models."
2. **Structural Landscape Tables**: MANDATORY. Create at least two Markdown tables:
   - *Mechanistic Summary Table*: Mapping molecules to pathways/cascades.
   - *Comparative Efficacy Table*: Benchmarking drugs/derivatives vs standard therapies or across different cancer lines.
   - **After each table, add a caption**: On a new line immediately following the table, write: "Table adapted from [First Author] et al., [Year]" citing the primary source(s) used for that table.
3. **Trial Identity Binding**: Explicitly map clinical findings to NCT IDs (National Clinical Trial IDs) when present in data. Link them to clinicaltrials.gov if possible.
4. **Molecular Granularity**: Avoid generic definitions. Instead of \"induces cell death\", describe \"Artemisinin-induced ferritinophagy via NCOA4 degradation triggering lipid peroxidation.\"
5. **Evidence Gap Analysis**: A good report admits what it doesn't know. Dedicate space in \"Future Directions\" to specific evidence voids found in the search context.
6. **Triple-Cite Core Claims**: For crucial mechanistic assertions, cite at least 3 distinct papers in a single sentence (e.g., Author A, 2021; Author B, 2023; Author C, 2024).

## SECTION WORD TARGETS (approximate):
- Executive Summary: 200 words
- Background and Clinical Context: 400 words
- Mechanisms of Action and Pharmacodynamics: 500 words (with table)
- Comparative Analysis and Efficacy: 500 words (with table)
- Safety Profiles and Adverse Events: 400 words
- Regulatory Framework and Approval Pathways: 250 words
- Economic Impact and Market Access: 200 words
- Conclusion and Future Directions: 350 words (including Evidence Gap Analysis)

## ABSOLUTE RULES:
1. NEVER output placeholders like \"[Up to N references]\", \"[citation needed]\".
2. GROUND EVERY CLAIM using the data provided in the GROUNDING DATA.
3. No code fences. Output raw Markdown text directly.
4. Start the report with an H1 title matching the research question exactly.
5. Use the following EXACT structure:
   # {state.research_question}
   ## Executive Summary
   ## Background and Clinical Context
   ## Mechanisms of Action and Pharmacodynamics
   ## Comparative Analysis and Efficacy
   ## Safety Profiles and Adverse Events
   ## Regulatory Framework and Approval Pathways
   ## Economic Impact and Market Access
   ## Conclusion and Future Directions
6. NEVER include a "References" section. We append this programmatically.
7. Use H3 (###) for subsections to ensure information-dense organization.
8. Cite heavily using APA in-text citations (Author, Year). YOU MUST CITE EVERY SOURCE YOU REFERENCE.
9. If data is unavailable for a benchmark, DO NOT use filler text. Keep it fact-dense.
10. **CITE ACCURATELY**: When you write (Author, Year), ensure Author matches the first author's surname from the GROUNDING DATA exactly. Do NOT invent or hallucinate citations.
"""

        # --- TIER 1: ELITE REPORT (Gemini via Pollinations, Massive Context) ---
        used_citations = sorted_citations[:60]  # Sonnet 4.5 has 256K context, increased from 30
        elite_findings_text = build_findings_text(used_citations)
        
        report_user_prompt_elite = f"""GROUNDING DATA — You MUST cite these sources extensively using APA format (Author, Year):
{elite_findings_text}

---
Research Question: {state.research_question}

Write the COMPLETE, EXHAUSTIVE report now. Do not stop until all sections are fully written."""

        try:
            state.progress_log.append(f"[{datetime.now().isoformat()}] Attempting Tier 1 Elite Report (Pollinations API, {len(used_citations)} sources)...")
            full_report_content = await self._call_llm(
                report_sys_prompt,
                report_user_prompt_elite,
                max_tokens=16384,  # Increased to allow denser 3000-word reports with tables
                mode="deep_research_elite",
                frequency_penalty=0.4,
                presence_penalty=0.4
            )
            state.progress_log.append(f"[{datetime.now().isoformat()}] Tier 1 Elite Report successfully generated!")
        except Exception as e:
            logger.warning(f"Tier 1 Elite Report failed: {e}. Falling back to Tier 2 Groq Lite Report.")
            
            # --- TIER 2: FALLBACK LITE REPORT (Groq Kimi, Small Context) ---
            state.progress_log.append(f"[{datetime.now().isoformat()}] Tier 1 exhausted. Triggering Tier 2 Fallback (Top 15 sources only)...")
            used_citations = sorted_citations[:15]
            lite_findings_text = build_findings_text(used_citations)
            
            report_user_prompt_lite = f"""GROUNDING DATA — You MUST cite these sources extensively using APA format (Author, Year):
{lite_findings_text}

---
Research Question: {state.research_question}

Write the COMPLETE, EXHAUSTIVE report now. Do not stop until all sections are fully written."""

            try:
                full_report_content = await self._call_llm(
                    report_sys_prompt, 
                    report_user_prompt_lite, 
                    max_tokens=12288,
                    mode="deep_research_single_pass",
                    frequency_penalty=0.4,
                    presence_penalty=0.4
                )
                state.progress_log.append(f"[{datetime.now().isoformat()}] Tier 2 Fallback Report successfully generated!")
            except Exception as e2:
                logger.error(f"Tier 2 Fallback Report also failed: {e2}")
                full_report_content = "The Research module encountered severe API rate limits across all providers and could not generate the text. However, the system successfully gathered the following bibliography:"

        # --- STAGE 2.5: SANITIZE FORMATTING ERRORS ---
        # Fix common LLM formatting issues like missing spaces between words
        def sanitize_spacing(text):
            # Fix camelCase concatenations (e.g., "spectrumsfrom" -> "spectrums from")
            # Pattern: lowercase followed immediately by uppercase
            text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
            
            # Fix specific known concatenations in medical/biological context
            replacements = [
                (r'([a-z])from\b', r'\1 from'),  # spectrumsfrom -> spectrums from
                (r'([a-z])to\b', r'\1 to'),      # resistantto -> resistant to
                (r'([a-z])in\b', r'\1 in'),      # increasedin -> increased in
                (r'([a-z])by\b', r'\1 by'),      # mediatedby -> mediated by
                (r'([a-z])via\b', r'\1 via'),    # transportvia -> transport via
                (r'([a-z])with\b', r'\1 with'),  # associatedwith -> associated with
                (r'([a-z])on\b', r'\1 on'),      # dependenton -> dependent on
                (r'([a-z])at\b', r'\1 at'),      # presentat -> present at
                (r'([a-z])for\b', r'\1 for'),    # responsiblefor -> responsible for
                (r'([a-z])as\b', r'\1 as'),      # suchas -> such as
                (r'([a-z])the\b', r'\1 the'),    # againstthe -> against the
                (r'([a-z])and\b', r'\1 and'),    # efficacyand -> efficacy and
                (r'([a-z])have\b', r'\1 have'),  # patientshave -> patients have
                (r'([a-z])has\b', r'\1 has'),    # resistancehas -> resistance has
                (r'([a-z])been\b', r'\1 been'),  # hasbeen -> has been
                (r'([a-z])were\b', r'\1 were'),  # theywere -> they were
                (r'([a-z])are\b', r'\1 are'),    # theyare -> they are
                (r'([a-z])was\b', r'\1 was'),    # itwas -> it was
                (r'([a-z])is\b', r'\1 is'),      # itis -> it is
                (r'([a-z])that\b', r'\1 that'),  # suggestedthat -> suggested that
                (r'([a-z])this\b', r'\1 this'),  # notedthis -> noted this
                (r'([a-z])these\b', r'\1 these'),  # usedthese -> used these
                (r'([a-z])their\b', r'\1 their'),  # intheir -> in their
                (r'([a-z])between\b', r'\1 between'),  # relationshipbetween -> relationship between
                (r'([a-z])among\b', r'\1 among'),  # distributedamong -> distributed among
                (r'([a-z])within\b', r'\1 within'),  # foundwithin -> found within
                (r'([a-z])during\b', r'\1 during'),  # observedduring -> observed during
                (r'([a-z])following\b', r'\1 following'),  # occurredfollowing -> occurred following
                (r'([a-z])without\b', r'\1 without'),  # patientswithout -> patients without
                (r'([a-z])under\b', r'\1 under'),  # studiedunder -> studied under
                (r'([a-z])over\b', r'\1 over'),  # administeredover -> administered over
                (r'([a-z])through\b', r'\1 through'),  # diffusedthrough -> diffused through
                (r'([a-z])into\b', r'\1 into'),  # convertedinto -> converted into
                (r'([a-z])onto\b', r'\1 onto'),  # loadedonto -> loaded onto
                (r'([a-z])upon\b', r'\1 upon'),  # dependentupon -> dependent upon
                (r'([a-z])across\b', r'\1 across'),  # distributedacross -> distributed across
                (r'([a-z])against\b', r'\1 against'),  # activityagainst -> activity against
                (r'([a-z])including\b', r'\1 including'),  # patientsincluding -> patients including
                (r'([a-z])involving\b', r'\1 involving'),  # casesinvolving -> cases involving
                (r'([a-z])requiring\b', r'\1 requiring'),  # interventionrequiring -> intervention requiring
                (r'([a-z])resulting\b', r'\1 resulting'),  # changesresulting -> changes resulting
                (r'([a-z])leading\b', r'\1 leading'),  # pathwayleading -> pathway leading
                (r'([a-z])causing\b', r'\1 causing'),  # mutationcausing -> mutation causing
                (r'([a-z])producing\b', r'\1 producing'),  # effectproducing -> effect producing
                (r'([a-z])binding\b', r'\1 binding'),  # drugbinding -> drug binding
                (r'([a-z])targeting\b', r'\1 targeting'),  # antibodytargeting -> antibody targeting
                (r'([a-z])resistant\b', r'\1 resistant'),  # multidrugresistant -> multidrug resistant
                (r'([a-z])sensitive\b', r'\1 sensitive'),  # antibioticsensitive -> antibiotic sensitive
                (r'([a-z])positive\b', r'\1 positive'),  # Grampositive -> Gram positive
                (r'([a-z])negative\b', r'\1 negative'),  # Gramnegative -> Gram negative
                (r'([a-z])specific\b', r'\1 specific'),  # targetspecific -> target specific
                (r'([a-z])dependent\b', r'\1 dependent'),  # pHdependent -> pH dependent
                (r'([a-z])independent\b', r'\1 independent'),  # doseindependent -> dose independent
                (r'([a-z])mediated\b', r'\1 mediated'),  # enzymemediated -> enzyme mediated
                (r'([a-z])induced\b', r'\1 induced'),  # stressinduced -> stress induced
                (r'([a-z])activated\b', r'\1 activated'),  # receptoractivated -> receptor activated
                (r'([a-z])regulated\b', r'\1 regulated'),  # generegulated -> gene regulated
                (r'([a-z])associated\b', r'\1 associated'),  # diseaseassociated -> disease associated
                (r'([a-z])related\b', r'\1 related'),  # drugrelated -> drug related
                (r'([a-z])induced\b', r'\1 induced'),  # druginduced -> drug induced
                (r'([a-z])derived\b', r'\1 derived'),  # plantderived -> plant derived
                (r'([a-z])based\b', r'\1 based'),  # evidencebased -> evidence based
                (r'([a-z])coated\b', r'\1 coated'),  # filmcoated -> film coated
                (r'([a-z])coated\b', r'\1 coated'),  # entericcoated -> enteric coated
                (r'([a-z])released\b', r'\1 released'),  # timedreleased -> time released
                (r'([a-z])soluble\b', r'\1 soluble'),  # watersoluble -> water soluble
                (r'([a-z])insoluble\b', r'\1 insoluble'),  # waterinsoluble -> water insoluble
                (r'([a-z])permeable\b', r'\1 permeable'),  # membranepermeable -> membrane permeable
                (r'([a-z])impermeable\b', r'\1 impermeable'),  # membraneimpermeable -> membrane impermeable
                (r'([a-z])selective\b', r'\1 selective'),  # nonselective -> non selective
                (r'([a-z])competitive\b', r'\1 competitive'),  # uncompetitive -> un competitive
                (r'([a-z])competitive\b', r'\1 competitive'),  # noncompetitive -> non competitive
                (r'([a-z])specific\b', r'\1 specific'),  # nonspecific -> non specific
            ]
            
            for pattern, replacement in replacements:
                text = re.sub(pattern, replacement, text)
            
            # Fix double spaces created by the replacements
            text = re.sub(r'  +', ' ', text)
            
            return text
        
        # Apply spacing sanitization
        original_length = len(full_report_content)
        full_report_content = sanitize_spacing(full_report_content)
        sanitized_length = len(full_report_content)
        
        if sanitized_length != original_length:
            logger.info(f"Sanitized report spacing: {original_length} -> {sanitized_length} chars ({sanitized_length - original_length} spacing fixes)")
        
        # --- STAGE 2.6: FILTER TO ACTUALLY-CITED REFERENCES ---
        # Scan the LLM-generated body for (Author, Year) patterns and only keep
        # citations that were actually referenced in-text.
        import re
        cited_patterns = re.findall(r'\(([A-Z][a-zA-Z]+(?:\s+et\s+al\.)?(?:\s+and\s+[A-Z][a-zA-Z]+)?),?\s*(\d{4})\)', full_report_content)
        cited_set = set()
        for author_match, year_match in cited_patterns:
            # Normalize: strip "et al." for matching
            author_key = author_match.replace(' et al.', '').strip().lower()
            cited_set.add((author_key, year_match))
        
        actually_cited = []
        for c in used_citations:
            # Extract first author surname from citation.authors
            first_author = ""
            if c.authors:
                first_author = c.authors.split(',')[0].strip().lower()
            c_year = (c.year or "").strip()
            
            if (first_author, c_year) in cited_set:
                actually_cited.append(c)
        
        # Fallback: if fewer than 3 matched (LLM used irregular citation format),
        # include ALL used_citations to avoid empty references
        if len(actually_cited) < 3:
            logger.warning(f"Only {len(actually_cited)} references matched in-text citations. Using all {len(used_citations)} as fallback.")
            actually_cited = list(used_citations)
        else:
            logger.info(f"Filtered references: {len(actually_cited)}/{len(used_citations)} actually cited in report body.")

        # Re-number citations sequentially for the final reference list
        for i, c in enumerate(actually_cited):
            c.id = i + 1

        # --- STAGE 3: ASSEMBLE REFERENCES ---
        refs_section = "## References\n\n"
        
        for citation in actually_cited:
            # No longer filtering out Tavily here to ensure all cited sources appear in list
            
            # Handle Authors
            authors = citation.authors.strip() if citation.authors else ""
            if not authors or authors.lower() == "unknown":
                author_part = ""
            else:
                # TRUNCATE MASSIVE AUTHOR LISTS (e.g., global consortium papers)
                # If there are more than 20 commas, assume >20 authors
                if authors.count(',') > 20:
                    first_author = authors.split(',')[0].strip()
                    authors = f"{first_author} et al."
                    
                author_part = authors if authors.endswith('.') else f"{authors}."
                author_part += " "
            
            # Handle Title
            title = citation.title.strip() if citation.title else ""
            title_part = title if title.endswith('.') else f"{title}."
            title_part += " "
            
            # Handle Source (Journal/Website)
            source = citation.source.strip() if citation.source else ""
            if source and source.lower() not in ["web", "unknown"]:
                # Remove common prefixes from journal titles if needed, but keeping it raw is safer
                source_part = f"{source} "
            else:
                source_part = ""
            
            # Handle Year
            year = citation.year.strip() if citation.year else ""
            year_part = f"({year}). " if year else "(n.d.). "
                
            # Handle Link — PREFER PubMed URL over DOI for accuracy.
            # Semantic Scholar DOIs are sometimes misattributed in their database.
            # PubMed URLs (pubmed.ncbi.nlm.nih.gov/{pmid}) are always accurate.
            link = ""
            if citation.pmid:
                link = f"https://pubmed.ncbi.nlm.nih.gov/{citation.pmid}/"
            elif citation.doi:
                doi_str = citation.doi.strip()
                link = f"https://doi.org/{doi_str}" if doi_str.startswith("10.") else doi_str
            elif citation.url:
                link = citation.url.strip()
                
            # Assemble the exact format requested: Author. Title. Journal (Year). Link
            if author_part:
                ref_line = f"{citation.id}. {author_part}{title_part}{source_part}{year_part}{link}"
            else:
                # If no author, title goes first
                ref_line = f"{citation.id}. {title_part}{source_part}{year_part}{link}"
                
            logger.debug(f"REF LOOP: {ref_line}")
            refs_section += ref_line.strip() + "\n"

        logger.debug(f"REFS_SECTION LEN: {len(refs_section)}")

        # Strip any LLM-generated references section (single source of truth = programmatic refs)
        response = full_report_content.strip()
        ref_header_index = response.rfind("## References")
        if ref_header_index != -1:
            response = response[:ref_header_index].rstrip()

        # Append programmatic references section
        response += f"\n\n---\n\n{refs_section}"

        # FIX: Title cleanup - Remove any "Deeply Researched Report:" prefix
        # and ensure the H1 matches the research question exactly
        lines = response.split('\n')
        if lines and lines[0].startswith('# '):
            # Replace the first line with the clean research question as H1
            lines[0] = f"# {state.research_question}"
            response = '\n'.join(lines)

        state.final_report = response
        state.status = "complete"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Report compilation complete ({len(response)} characters)")
        
        return state
    
    # ========================================================================
    # MAIN WORKFLOW EXECUTION
    # ========================================================================
    
    async def run_research(self, question: str, user_id: UUID) -> ResearchState:
        """
        Execute the full deep research workflow
        """
        # Initialize state
        state = ResearchState(research_question=question)
        state.progress_log.append(f"[{datetime.now().isoformat()}] Deep Research initiated for: {question[:100]}...")
        
        try:
            # Node A: Planning
            logger.info(f"📍 Deep Research: Starting Planning Phase for question='{question[:50]}...'")
            plan_start = datetime.now()
            state = await self._node_planner(state)
            logger.info(f"✅ Deep Research: Planning Complete ({state.plan_overview[:50]}...) - Duration: {(datetime.now() - plan_start).total_seconds():.2f}s")
            
            if state.error_message:
                state.status = "error"
                return state
            
            # Node B: Researching
            logger.info(f"📍 Deep Research: Starting Research Phase with {len(state.steps)} steps")
            research_start = datetime.now()
            state = await self._node_researcher(state)
            logger.info(f"✅ Deep Research: Research Complete (Found {len(state.findings)} sources) - Duration: {(datetime.now() - research_start).total_seconds():.2f}s")
            
            # Node C: Reviewing
            logger.info("📍 Deep Research: Starting Review Phase")
            review_start = datetime.now()
            state = await self._node_reviewer(state)
            logger.info(f"✅ Deep Research: Review Complete (Validated {len(state.citations)} citations) - Duration: {(datetime.now() - review_start).total_seconds():.2f}s")
            
            # Node D: Writing
            logger.info("📍 Deep Research: Starting Writing Phase")
            write_start = datetime.now()
            state = await self._node_writer(state)
            logger.info(f"✅ Deep Research: Writing Complete - Duration: {(datetime.now() - write_start).total_seconds():.2f}s")
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            state.progress_log.append(f"[{datetime.now().isoformat()}] ERROR: {e}")
        
        return state
    
    async def run_research_streaming(self, question: str, user_id: UUID):
        # Execute deep research with streaming progress updates
        # Yields JSON progress updates
        state = ResearchState(research_question=question)
        
        yield json.dumps({
            "type": "status",
            "status": "initializing",
            "message": "Starting deep research...",
            "progress": 0
        })
        
        try:
            # Node A: Planning
            logger.info(f"📍 [Streaming] Deep Research: Starting Planning Phase")
            plan_start = datetime.now()
            
            yield json.dumps({
                "type": "status",
                "status": "planning",
                "message": "Analyzing query and creating research plan...",
                "progress": 10
            })
            
            state = await self._node_planner(state)
            logger.info(f"✅ [Streaming] Deep Research: Planning Complete - Duration: {(datetime.now() - plan_start).total_seconds():.2f}s")
            
            if state.error_message:
                yield json.dumps({
                    "type": "error",
                    "message": state.error_message
                })
                return
            
            yield json.dumps({
                "type": "plan",
                "plan_overview": state.plan_overview,
                "steps": [{"id": s.id, "topic": s.topic, "source": s.source_preference} for s in state.steps],
                "progress": 20
            })
            
            # Node B: Researching
            logger.info(f"📍 [Streaming] Deep Research: Starting Research Phase with {len(state.steps)} steps")
            research_start = datetime.now()
            
            yield json.dumps({
                "type": "status",
                "status": "researching",
                "message": f"Searching {len(state.steps)} research topics...",
                "progress": 30
            })
            
            state = await self._node_researcher(state)
            
            logger.info(f"✅ [Streaming] Deep Research: Research Complete (Found {len(state.findings)} sources) - Duration: {(datetime.now() - research_start).total_seconds():.2f}s")
            
            # Send findings WITH preliminary citations so sources appear immediately
            preliminary_citations = []
            for i, f in enumerate(state.findings[:30]):  # Preview first 30 sources
                preliminary_citations.append({
                    "id": i + 1,
                    "title": f.title,
                    "url": f.url,
                    "source": f.source,
                    "source_type": f.source,
                    "authors": "",  # Will be enriched in review phase
                    "year": "",
                    "snippet": f.raw_content[:200] + "..." if len(f.raw_content) > 200 else f.raw_content
                })
            
            yield json.dumps({
                "type": "findings",
                "count": len(state.findings),
                "message": f"Found {len(state.findings)} relevant sources",
                "progress": 60,
                "citations": preliminary_citations  # Send sources immediately!
            })
            
            # Node C: Reviewing
            logger.info("📍 [Streaming] Deep Research: Starting Review Phase")
            review_start = datetime.now()
            
            yield json.dumps({
                "type": "status",
                "status": "reviewing",
                "message": "Processing biomedical data sources...",
                "progress": 70
            })
            
            state = await self._node_reviewer(state)
            logger.info(f"✅ [Streaming] Deep Research: Review Complete (Validated {len(state.citations)} citations) - Duration: {(datetime.now() - review_start).total_seconds():.2f}s")
            
            yield json.dumps({
                "type": "citations",
                "count": len(state.citations),
                "message": f"Validated {len(state.citations)} citations",
                "progress": 80,
                "citations": [
                    {
                        "id": c.id, 
                        "title": c.title, 
                        "url": c.url, 
                        "source": c.source,
                        "source_type": c.source,  # PubMed, Google Scholar, or Web
                        "authors": c.authors or "",
                        "year": c.year or "",
                        "snippet": c.abstract[:200] + "..." if c.abstract and len(c.abstract) > 200 else (c.abstract or "")
                    }
                    for c in state.citations
                ]
            })
            
            # Node D: Writing
            logger.info("📍 [Streaming] Deep Research: Starting Writing Phase")
            write_start = datetime.now()
            
            yield json.dumps({
                "type": "status",
                "status": "writing",
                "message": "Synthesizing research report...",
                "progress": 90
            })
            
            state = await self._node_writer(state)
            logger.info(f"✅ [Streaming] Deep Research: Writing Complete - Duration: {(datetime.now() - write_start).total_seconds():.2f}s")
            
            # Final report with full APA citation data
            yield json.dumps({
                "type": "complete",
                "status": "complete",
                "report": state.final_report,
                "citations": [
                    {
                        "id": c.id, 
                        "title": c.title, 
                        "url": c.url, 
                        "source": c.source,
                        "source_type": c.source,  # PubMed, Google Scholar, or Web
                        "authors": c.authors or "",
                        "year": c.year or "",
                        "journal": c.source if c.source != "Web" else "",
                        "doi": c.doi or "",
                        "snippet": c.abstract[:300] + "..." if c.abstract and len(c.abstract) > 300 else (c.abstract or "")
                    }
                    for c in state.citations
                ],
                "progress": 100
            })
            
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e)
            })
