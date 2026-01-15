"""
Deep Research Service
LangGraph-style autonomous research agent for biomedical literature review
"""

import os
import json
import httpx
import asyncio
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List, TypedDict, AsyncGenerator
from dataclasses import dataclass, field
from uuid import UUID
from datetime import datetime
from supabase import Client

from app.core.config import settings


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
    max_iterations: int = 5
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
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.serp_api_key = os.getenv("SERP_API_KEY")
        self.serper_api_key = os.getenv("SERPER_API_KEY")
    
    async def search_pubmed(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search PubMed using NCBI E-utilities
        Returns list of { title, abstract, pmid, doi, authors, journal, year }
        """
        results = []
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Step 1: Search for PMIDs
                search_url = f"{self.pubmed_base_url}/esearch.fcgi"
                search_params = {
                    "db": "pubmed",
                    "term": query,
                    "retmax": max_results,
                    "retmode": "json",
                    "sort": "relevance"
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
                    "retmode": "xml"
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
                        
                        # Extract title
                        title_elem = article_data.find(".//ArticleTitle")
                        title = title_elem.text if title_elem is not None else "No title"
                        
                        # Extract abstract
                        abstract_elem = article_data.find(".//Abstract/AbstractText")
                        abstract = abstract_elem.text if abstract_elem is not None else ""
                        
                        # Extract authors
                        authors = []
                        for author in article_data.findall(".//Author"):
                            last_name = author.find("LastName")
                            if last_name is not None:
                                authors.append(last_name.text)
                        author_str = ", ".join(authors[:3])
                        if len(authors) > 3:
                            author_str += " et al."
                        
                        # Extract journal
                        journal_elem = article_data.find(".//Journal/Title")
                        journal = journal_elem.text if journal_elem is not None else ""
                        
                        # Extract year
                        year_elem = article_data.find(".//Journal/JournalIssue/PubDate/Year")
                        year = year_elem.text if year_elem is not None else ""
                        
                        # Extract DOI
                        doi = ""
                        for id_elem in article.findall(".//ArticleId"):
                            if id_elem.get("IdType") == "doi":
                                doi = id_elem.text
                                break
                        
                        results.append({
                            "title": title,
                            "abstract": abstract or "[Abstract not available]",
                            "pmid": pmid,
                            "doi": doi,
                            "authors": author_str,
                            "journal": journal,
                            "year": year,
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                        })
                        
                    except Exception as e:
                        print(f"Error parsing article: {e}")
                        continue
                        
        except Exception as e:
            print(f"PubMed search error: {e}")
        
        return results
    
    async def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web using Tavily or fallback to DuckDuckGo
        Returns list of { title, snippet, url }
        """
        results = []
        
        # Try Tavily first if API key is available
        if self.tavily_api_key:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        "https://api.tavily.com/search",
                        json={
                            "api_key": self.tavily_api_key,
                            "query": query,
                            "search_depth": "advanced",
                            "max_results": max_results,
                            "include_domains": [
                                "fda.gov", "nih.gov", "clinicaltrials.gov",
                                "drugs.com", "medscape.com", "nature.com",
                                "sciencedirect.com", "springer.com"
                            ]
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        for result in data.get("results", []):
                            results.append({
                                "title": result.get("title", ""),
                                "snippet": result.get("content", ""),
                                "url": result.get("url", "")
                            })
                        return results
                        
            except Exception as e:
                print(f"Tavily search error: {e}")
        
        # Fallback: Use DuckDuckGo HTML search (no API key needed)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://html.duckduckgo.com/html/",
                    params={"q": f"{query} site:nih.gov OR site:fda.gov OR site:pubmed.ncbi.nlm.nih.gov"},
                    headers={"User-Agent": "Mozilla/5.0 (compatible; PharmGPT/1.0)"}
                )
                
                # Simple parsing of DuckDuckGo HTML results
                from html.parser import HTMLParser
                
                class DDGParser(HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self.results = []
                        self.current_result = {}
                        self.in_result = False
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
                
                parser = DDGParser()
                parser.feed(response.text)
                results = parser.results[:max_results]
                
        except Exception as e:
            print(f"Web search error: {e}")
        
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
                    headers={"User-Agent": "Mozilla/5.0 (compatible; PharmGPT/1.0)"}
                )
                
                if response.status_code == 200:
                    from html.parser import HTMLParser
                    
                    class DDGParser(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.results = []
                            self.current_result = {}
                            self.in_result = False
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
            print(f"DuckDuckGo search error: {e}")
            
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
            print("SERP_API_KEY not configured, skipping Google Scholar search")
            return results
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                        
                        # Parse authors
                        authors_list = publication_info.get("authors", [])
                        authors = ", ".join([a.get("name", "") for a in authors_list[:3]])
                        if len(authors_list) > 3:
                            authors += " et al."
                        
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
                            "source": "Google Scholar"
                        })
                    
                    return results[:max_results]
                else:
                    print(f"SERP API error: {response.status_code}")
                    
        except Exception as e:
            print(f"Google Scholar search error: {e}")
        
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
            print(f"Serper search error: {e}")
        return results


# ============================================================================
# DEEP RESEARCH SERVICE
# ============================================================================

class DeepResearchService:
    """
    Autonomous research agent using LangGraph-style workflow
    Nodes: Planner -> Researcher -> Reviewer -> Writer
    """
    
    def __init__(self, db: Client):
        self.db = db
        self.tools = ResearchTools()
        self.mistral_api_key = settings.MISTRAL_API_KEY
        self.mistral_base_url = "https://api.mistral.ai/v1"
        self.miroflow_path = "/var/www/MiroFlow"
        self.venv_python = "/home/ubuntu/.local/bin/uv"

    async def run_miroflow_research(self, question: str, user_id: UUID) -> AsyncGenerator[str, None]:
        """
        Runs MiroFlow deep research and yields output line by line as SSE events.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # Default config - can be made dynamic
        config_file = "agent_quickstart_reading"
        
        # Check if MiroFlow exists
        if not os.path.exists(self.miroflow_path):
             yield json.dumps({"type": "error", "message": "MiroFlow not found on server."})
             return

        # Prepare environment variables
        env = os.environ.copy()
        # Map Mistral to OpenAI schema for MiroFlow
        env["OPENAI_API_KEY"] = self.mistral_api_key or env.get("MISTRAL_API_KEY", "")
        env["OPENAI_BASE_URL"] = "https://api.mistral.ai/v1"
        # Ensure Tools keys are present
        env["TAVILY_API_KEY"] = env.get("TAVILY_API_KEY", "")
        env["SERP_API_KEY"] = env.get("SERP_API_KEY", "")
        
        # Override model via Hydra syntax if possible, or assume env var suffices?
        # We'll add Hydra overrides to the command
        
        
        # Determine UV path (fallback to just 'uv' if not sure, but try explicit first)
        uv_path = "/home/ubuntu/.local/bin/uv"
        if not os.path.exists(uv_path):
            uv_path = "uv"

        cmd = [
            uv_path, "run", "main.py", "trace",
            f"--config_file_name={config_file}",
            f"--task={question}",
            "main_agent.llm.provider_class=GPTOpenAIClient",
            "main_agent.llm.model_name=mistral-large-latest",
            "+main_agent.llm.openai_api_key=${oc.env:OPENAI_API_KEY}",
            "+main_agent.llm.openai_base_url=${oc.env:OPENAI_BASE_URL}"
        ]
        
        logger.info(f"🚀 Starting Deep Research (MiroFlow) with Mistral: {question}")
        logger.info(f"📂 CWD: {self.miroflow_path}")
        logger.info(f"⚙️ Command: {' '.join(cmd)}")
        
        yield json.dumps({"type": "status", "status": "initializing", "message": "Initializing Research Agent (Mistral)..."})
        
        try:
            process = await asyncio.create_subprocess_exec(
                cmd[0], *cmd[1:], # Unpack args properly
                # "llm.provider=openai", # Assuming default is openai or consistent
                cwd=self.miroflow_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )

            # Regex patterns for parsing
            import re
            re_step = re.compile(r"Step\s+(\d+)/(\d+)", re.IGNORECASE)
            re_source = re.compile(r"(https?://\S+)") # Naive URL extractor
            re_thinking = re.compile(r"(Thinking|Action|Observation):\s*(.*)", re.IGNORECASE)

            final_report_buffer = []

            if process.stdout:
                async for line in process.stdout:
                    decoded = line.decode().strip()
                    if not decoded:
                        continue
                        
                    # 1. Parse Progress (Step X/Y)
                    step_match = re_step.search(decoded)
                    if step_match:
                        current_step, total_steps = step_match.groups()
                        percent = int((int(current_step) / int(total_steps)) * 100)
                        yield json.dumps({
                            "type": "status",
                            "status": "researching",
                            "message": f"Step {current_step}/{total_steps}: Processing...",
                            "progress": percent
                        })
                    
                    # 2. Parse Sources (Any URL in text)
                    # Note: this is heuristic. Ideally MiroFlow outputs "Source: <url>"
                    # We filter out internal/uninteresting URLs if needed
                    url_match = re_source.search(decoded)
                    if url_match:
                        url = url_match.group(1)
                        if "api.mistral.ai" not in url and "openai" not in url:
                             yield json.dumps({
                                "type": "citations",
                                "citations": [{
                                    "id": hash(url) % 1000, # Fake ID for now
                                    "title": "Web Source", # Placeholder until title extraction
                                    "url": url,
                                    "snippet": decoded[:100] + "...",
                                    "source_type": "Web"
                                }]
                            })

                    # 3. Parse Thinking/Action
                    action_match = re_thinking.search(decoded)
                    if action_match:
                        action_type, action_text = action_match.groups()
                        yield json.dumps({
                            "type": "status",
                            "status": "researching",
                            "message": f"{action_type}: {action_text[:50]}...",
                        })

                    # 4. Accumulate Final Report (heuristic)
                    # If we see a large block of text at the end, it's likely the report.
                    # For now, just stream everything as debug info too
                    # yield json.dumps({"type": "progress", "message": decoded})
                    
                    # Capture everything to final buffer just in case
                    final_report_buffer.append(decoded)

            # Wait for completion
            await process.wait()
            
            # Read stderr if failure
            if process.returncode != 0:
                err = ""
                if process.stderr:
                    err_bytes = await process.stderr.read()
                    err = err_bytes.decode()
                yield json.dumps({"type": "error", "message": f"MiroFlow failed: {err}"})
            else:
                # Try to extract the Markdown report from the buffer
                # Look for the last "Answer:" or just join the last N lines?
                # For now, simple join
                full_log = "\n".join(final_report_buffer)
                yield json.dumps({
                    "type": "complete", 
                    "report": full_log,
                    "status": "complete"
                })


        except Exception as e:
            logger.error(f"Research failed: {e}")
            yield json.dumps({"type": "error", "message": str(e)})

    
    async def _call_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = False, max_tokens: int = 4000) -> str:
        """
        Call Mistral LLM with robust fallback strategy.
        Sequence: mistral-large-latest -> mistral-medium-latest -> mistral-small-latest
        """
        from app.utils.rate_limiter import mistral_limiter
        
        # Models to try in order of capability
        models_to_try = [
            "mistral-large-latest",   # Best reasoning
            "mistral-medium-latest",  # Good balance
            "mistral-small-latest"    # Reliable/Fast fallback
        ]
        
        last_error = None
        
        for model in models_to_try:
            try:
                # Apply rate limit before EACH call attempt
                await mistral_limiter.wait_for_slot()
                
                print(f"🔬 Deep Research: Attempting with model {model}...")
                
                async with httpx.AsyncClient(timeout=180.0) as client:  # Increased timeout for longer responses
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3 if json_mode else 0.7,
                        "max_tokens": max_tokens
                    }
                    
                    if json_mode:
                        payload["response_format"] = {"type": "json_object"}
                    
                    response = await client.post(
                        f"{self.mistral_base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.mistral_api_key}",
                            "Content-Type": "application/json"
                        },
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result["choices"][0]["message"]["content"]
                        if not content:
                            raise ValueError("Empty content from LLM")
                        return content
                    
                    elif response.status_code in [401, 403, 404, 429]:
                        # Auth/Rate/Model errors -> Try next model immediately
                        print(f"⚠️ Model {model} failed (Status {response.status_code}): {response.text}")
                        last_error = f"Status {response.status_code}"
                        continue
                    else:
                        # Other errors -> Log and try next
                        print(f"⚠️ Model {model} error: {response.text}")
                        last_error = f"Status {response.status_code}"
                        continue
                        
            except Exception as e:
                print(f"⚠️ Model {model} exception: {e}")
                last_error = str(e)
                continue
        
        # If all failed
        print(f"❌ CRITICAL: All Deep Research models failed. Last error: {last_error}")
        # Return a valid JSON error structure if json_mode was requested, to prevent downstream crash
        if json_mode:
            return '{"error": "Deep Research unavailable due to model failures", "plan_overview": "Research failed", "steps": []}'
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

STEP 2 - CREATE 4 STRATEGIC SUB-TOPICS:
Based on the identified domain, break down the question into 4 complementary sub-topics.
Each sub-topic must:
- Be specific and actionable (not vague)
- Use precise scientific terminology
- Cover a distinct aspect (no overlap)
- Include 3-5 relevant keywords for searching

STEP 3 - ASSIGN SOURCE PREFERENCES:
- "PubMed" for: peer-reviewed research, clinical data, molecular mechanisms
- "Web" for: guidelines, protocols, current news, FDA approvals, clinical trial registries

RETURN FORMAT (strict JSON):
{
    "plan_overview": "2-3 sentences describing: (1) identified domain, (2) research strategy, (3) expected outcome",
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
        }
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
        """
        state.status = "researching"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Starting multi-source literature search...")
        
        for step in state.steps:
            if step.status == "completed":
                continue
                
            step.status = "in_progress"
            state.progress_log.append(f"[{datetime.now().isoformat()}] Researching: {step.topic}")
            
            # Generate optimized search queries
            query_prompt = f"""Convert this research topic into effective search queries:
Topic: {step.topic}
Keywords: {', '.join(step.keywords)}

Generate 2 search queries.
Return as JSON: {{"queries": ["query1", "query2"]}}"""

            query_response = await self._call_llm(
                "You are a search specialist. Generate precise biomedical search queries.",
                query_prompt,
                json_mode=True
            )
            
            try:
                queries_data = json.loads(query_response)
                queries = queries_data.get("queries", [" ".join(step.keywords)])
            except:
                queries = [" ".join(step.keywords)]
            
            # Execute searches
            step_findings_count = 0
            
            for query in queries:
                # Parallel Search: PubMed, Web (Tavily), DuckDuckGo, Google Scholar, Serper
                tasks = [
                    self.tools.search_pubmed(query, max_results=3),
                    self.tools.search_web(query, max_results=3),
                    self.tools.search_duckduckgo(query, max_results=3),
                    self.tools.search_google_scholar(query, max_results=3),
                    self.tools.search_serper(query, max_results=3)
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                results_pubmed = results[0] if not isinstance(results[0], Exception) else []
                results_web = results[1] if not isinstance(results[1], Exception) else []
                results_ddg = results[2] if not isinstance(results[2], Exception) else []
                results_scholar = results[3] if not isinstance(results[3], Exception) else []
                results_serper = results[4] if not isinstance(results[4], Exception) else []
                
                # Process PubMed Results
                for r in results_pubmed:
                    finding = Finding(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        source="PubMed",
                        raw_content=r.get("abstract", ""),
                        data_limitation="Abstract Only" if not r.get("full_text") else None
                    )
                    finding._pubmed_data = {
                        "authors": r.get("authors", ""),
                        "year": r.get("year", ""),
                        "journal": r.get("journal", ""),
                        "doi": r.get("doi", ""),
                        "pmid": r.get("pmid", "")
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
                        raw_content=r.get("snippet", "")
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

                # Process Google Scholar Results
                for r in results_scholar:
                    finding = Finding(
                        title=r.get("title", ""),
                        url=r.get("url", ""),
                        source="Google Scholar",
                        raw_content=r.get("snippet", "")
                    )
                    # Store rich metadata for citation formatting
                    finding._pubmed_data = {
                        "authors": r.get("authors", ""),
                        "year": r.get("year", ""),
                        "journal": "Google Scholar", # Or extract if available
                        "doi": "", # Scholar doesn't always give DOI directly
                        "cited_by": r.get("cited_by", 0)
                    }
                    if self._is_valid_finding(finding):
                        step.findings.append(finding)
                        state.findings.append(finding)
                        step_findings_count += 1

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
            state.progress_log.append(f"[{datetime.now().isoformat()}] Found {step_findings_count} sources for: {step.topic}")
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        state.iteration_count += 1
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
        for i, f in enumerate(state.findings[-30:]):  # Review last 30 findings
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
            "}"
        )

        user_prompt = f"Research Question: {state.research_question}\n\nFindings Summary:\n{findings_text}"
        
        response = await self._call_llm(system_prompt, user_prompt, json_mode=True)
        
        try:
            review = json.loads(response)
            
            if not review.get("sufficient", True) and state.iteration_count < state.max_iterations:
                state.progress_log.append(f"[{datetime.now().isoformat()}] Gaps detected: {review.get('missing_info')}. Recursion triggered.")
                
                # Add new steps for recursion
                new_queries = review.get("new_queries", [])
                for i, query in enumerate(new_queries):
                    new_step = ResearchStep(
                        id=len(state.steps) + 1,
                        topic=f"Gap Fill: {query}",
                        keywords=query.split(),
                        source_preference="Web" # Default to web for gap filling
                    )
                    state.steps.append(new_step)
                
                # Reset status to trigger researcher again
                # Note: In a real graph, we'd route back. Here we simulate by appending steps and letting the loop continue if we were looping.
                # Since we are in a linear flow, we need to explicitly call researcher again or handle this in the main loop.
                # For this implementation, we will recursively call _node_researcher immediately for the new steps.
                await self._node_researcher(state)
            
            else:
                state.progress_log.append(f"[{datetime.now().isoformat()}] Research sufficient. Proceeding to writing.")
                
                # Process citations for the writer
                citation_id = 1
                for f in state.findings:
                     # Deduplicate based on title
                    if not any(c.title == f.title for c in state.citations):
                        pubmed_data = getattr(f, '_pubmed_data', None)
                        
                        # Filter out Web/DDG results that look like academic papers but lack metadata
                        # This prevents "Title Only" citations for scientific sources
                        if not pubmed_data and f.source in ["Web", "DuckDuckGo"]:
                            # Heuristic: Long titles or academic keywords usually imply a paper
                            is_likely_paper = len(f.title) > 60 or any(w in f.title.lower() for w in ["study", "analysis", "effect of", "role of", "clinical", "mechanism"])
                            if is_likely_paper:
                                continue

                        citation = Citation(
                            id=citation_id,
                            title=f.title,
                            authors=pubmed_data.get("authors", "") if pubmed_data else "",
                            source=pubmed_data.get("journal", f.source) if pubmed_data else f.source,
                            url=f.url,
                            doi=pubmed_data.get("doi", "") if pubmed_data else None,
                            pmid=pubmed_data.get("pmid", "") if pubmed_data else None,
                            year=pubmed_data.get("year", "") if pubmed_data else None,
                            data_limitation=f.data_limitation
                        )
                        state.citations.append(citation)
                        citation_id += 1
            
        except json.JSONDecodeError:
            state.progress_log.append(f"[{datetime.now().isoformat()}] Review parsing error. Proceeding.")
        
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
        
        # Handle empty results
        if not state.citations and not state.findings:
            state.final_report = f"# Research Report: {state.research_question}\n\nNo significant data found."
            state.status = "complete"
            return state

        # Prepare validated findings
        findings_text = ""
        for i, citation in enumerate(state.citations[:40]): # Increase context
            finding = next((f for f in state.findings if f.title == citation.title), None)
            if finding:
                findings_text += f"\n[{citation.id}] {citation.title}\n"
                findings_text += f"   Authors: {citation.authors or 'Unknown'}\n"
                findings_text += f"   Source: {citation.source} | Year: {citation.year or 'n.d.'}\n"
                if citation.doi:
                    findings_text += f"   DOI: {citation.doi}\n"
                findings_text += f"   Key Content: {finding.raw_content[:500]}\n"
        
        system_prompt = """You are a senior medical/scientific research analyst. Generate a comprehensive, well-structured research report.

## DOCUMENT STRUCTURE:

### 1. TITLE
Start with a clear, scientific title as an H1 heading:
```
# [Clear, Specific Title Based on the Research Question]
```

### 2. EXECUTIVE SUMMARY
A brief blockquote with 3-5 key takeaways:
```
> **Key Findings:**
> - [Most important finding]
> - [Second key point]
> - [Clinical/practical implication]
```

### 3. MAIN CONTENT
Structure your sections INTELLIGENTLY based on what the research question requires. Do NOT use fixed templates.

Examples of adaptive section structures:
- For a drug/treatment question: Background, Mechanism, Clinical Evidence, Safety, Conclusions
- For a disease question: Pathophysiology, Diagnosis, Treatment Options, Prognosis
- For a comparison question: Overview, Comparison Criteria, Analysis, Recommendations
- For a methodology question: Principles, Protocol, Applications, Limitations
- For a mechanism question: Molecular Basis, Pathway Analysis, Regulatory Factors, Clinical Relevance

Use H2 (##) for main sections and H3 (###) for subsections.

### 4. KNOWLEDGE GAPS (Important)
Include a section discussing what is NOT known or where evidence is conflicting. This is valuable.

### 5. REFERENCES
List all cited sources in APA 7th edition format.

## CITATION FORMAT (APA 7th Edition):

In-text examples:
- "...associated with significant toxicity (Khanna et al., 2015)."
- "Jordan et al. (2015) demonstrated that..."
- Two authors: "(Kwan & Brodie, 2021)"

Reference format:
```
Author, A. A., Author, B. B., & Author, C. C. (Year). Title of article. *Journal Name, Volume*(Issue), Pages. doi:10.xxxx/xxxxx
```

## WRITING STYLE RULES (CRITICAL):
1. Write in clear, professional scientific prose
2. AVOID BOLD TEXT - Maximum 2 bold terms in the ENTIRE document:
   - Only for critical drug names or safety warnings
   - Never bold entire phrases or sentences
   - Use italics for emphasis instead
3. Synthesize across sources - don't summarize each source individually
4. Every major claim needs an in-text citation
5. Be comprehensive but readable - aim for 2000+ words
6. Use plain language where possible, technical terms only when necessary
7. Output raw Markdown only (no code blocks wrapping the document)
8. Do NOT include metadata like "Status: Complete" or "Sources Analyzed" in the output
9. Alphabetize the References section by first author's last name
10. TABLES: When including comparison tables or data tables:
    - Always include a caption below the table
    - Caption must state the source: "Table adapted from [Author et al., Year]" or "Data compiled from [Author1, Year; Author2, Year]"
    - Example format:
      | Drug | Dose | Efficacy |
      |------|------|----------|
      | Drug A | 10mg | 85% |
      *Table 1: Comparison of efficacy. Adapted from Smith et al. (2023).*"""


        user_prompt = f"""Research Question: {state.research_question}

Research Context (Use these sources for citations):
{findings_text}

Generate a comprehensive research report. Structure the sections intelligently based on what this specific question requires - do not use a fixed template."""

        # Use higher token limit for complete report with references
        response = await self._call_llm(system_prompt, user_prompt, json_mode=False, max_tokens=20000)
        
        state.final_report = response
        state.status = "complete"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Report complete ({len(response)} characters)")
        
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
            
            yield json.dumps({
                "type": "findings",
                "count": len(state.findings),
                "message": f"Found {len(state.findings)} relevant sources",
                "progress": 60
            })
            
            # Node C: Reviewing
            logger.info("📍 [Streaming] Deep Research: Starting Review Phase")
            review_start = datetime.now()
            
            yield json.dumps({
                "type": "status",
                "status": "reviewing",
                "message": "Analyzing and validating sources...",
                "progress": 70
            })
            
            state = await self._node_reviewer(state)
            logger.info(f"✅ [Streaming] Deep Research: Review Complete (Validated {len(state.citations)} citations) - Duration: {(datetime.now() - review_start).total_seconds():.2f}s")
            
            yield json.dumps({
                "type": "citations",
                "count": len(state.citations),
                "message": f"Validated {len(state.citations)} citations",
                "progress": 80
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
