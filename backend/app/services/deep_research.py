"""
Deep Research Service
LangGraph-style autonomous research agent for biomedical literature review
"""

import os
import json
import httpx
import asyncio
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any, List, TypedDict
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
    
    async def _call_llm(self, system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
        """Call Mistral LLM"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": "mistral-large-latest",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3 if json_mode else 0.7,
                    "max_tokens": 4000
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
                    return result["choices"][0]["message"]["content"]
                else:
                    print(f"LLM error: {response.status_code} - {response.text}")
                    return ""
                    
        except Exception as e:
            print(f"LLM call error: {e}")
            return ""

    # ========================================================================
    # NODE A: THE PLANNER (Deconstructor)
    # ========================================================================
    
    async def _node_planner(self, state: ResearchState) -> ResearchState:
        """
        Break down the research question into sub-topics using PICO/MoA framework
        """
        state.status = "planning"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Starting research planning...")
        
        system_prompt = """You are the Lead Research Investigator for PharmGPT. Your goal is to break down complex biomedical queries into a structured research plan.

**Context:**
The user is asking a question related to drug discovery, pharmacology, or clinical medicine. You must structure the investigation to cover all necessary scientific angles.

**Instructions:**
1. Analyze the User's Query
2. Deconstruct it using the PICO framework (Population, Intervention, Comparison, Outcome) if applicable, or a Target/MoA/ADMET framework if it is a discovery query.
3. Generate a list of 3-5 distinct "Research Steps" (Sub-topics) that must be investigated to answer the query fully.
4. For each step, identify the best data source:
   - "PubMed" for biological mechanisms, clinical trials, and animal studies.
   - "Web" for latest news, commercial drug pipeline status, or FDA approvals.

**Output Format (JSON):**
{
  "plan_overview": "A 1-sentence summary of the strategy.",
  "steps": [
    {
      "id": 1,
      "topic": "Mechanism of Action in TME",
      "keywords": ["PD-1 blockade", "tumor microenvironment", "exhaustion"],
      "source_preference": "PubMed"
    }
  ]
}"""

        user_prompt = f"Research Question: {state.research_question}"
        
        response = await self._call_llm(system_prompt, user_prompt, json_mode=True)
        
        try:
            plan = json.loads(response)
            state.plan_overview = plan.get("plan_overview", "")
            
            for step_data in plan.get("steps", []):
                step = ResearchStep(
                    id=step_data.get("id", len(state.steps) + 1),
                    topic=step_data.get("topic", ""),
                    keywords=step_data.get("keywords", []),
                    source_preference=step_data.get("source_preference", "PubMed")
                )
                state.steps.append(step)
            
            state.progress_log.append(f"[{datetime.now().isoformat()}] Plan created with {len(state.steps)} research steps")
            
        except json.JSONDecodeError as e:
            state.error_message = f"Failed to parse research plan: {e}"
            state.progress_log.append(f"[{datetime.now().isoformat()}] ERROR: {state.error_message}")
        
        return state
    
    # ========================================================================
    # NODE B: THE RESEARCHER (The Looper)
    # ========================================================================
    
    async def _node_researcher(self, state: ResearchState) -> ResearchState:
        """
        Execute searches for each sub-topic using PubMed and Web tools
        """
        state.status = "researching"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Starting literature search...")
        
        for step in state.steps:
            if step.status == "completed":
                continue
                
            step.status = "in_progress"
            state.progress_log.append(f"[{datetime.now().isoformat()}] Researching: {step.topic}")
            
            # Generate optimized search queries
            query_prompt = f"""Convert this research topic into effective search queries:
Topic: {step.topic}
Keywords: {', '.join(step.keywords)}

Generate 2 search queries optimized for {step.source_preference}. Use Boolean operators (AND, OR) and scientific terminology.
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
            for query in queries:
                if step.source_preference == "PubMed":
                    results = await self.tools.search_pubmed(query, max_results=5)
                    for r in results:
                        finding = Finding(
                            title=r.get("title", ""),
                            url=r.get("url", ""),
                            source="PubMed",
                            raw_content=r.get("abstract", ""),
                            data_limitation="Abstract Only" if not r.get("full_text") else None
                        )
                        # Store PubMed metadata for APA citations
                        finding._pubmed_data = {
                            "authors": r.get("authors", ""),
                            "year": r.get("year", ""),
                            "journal": r.get("journal", ""),
                            "doi": r.get("doi", ""),
                            "pmid": r.get("pmid", "")
                        }
                        step.findings.append(finding)
                        state.findings.append(finding)
                else:
                    results = await self.tools.search_web(query, max_results=3)
                    for r in results:
                        finding = Finding(
                            title=r.get("title", ""),
                            url=r.get("url", ""),
                            source="Web",
                            raw_content=r.get("snippet", "")
                        )
                        step.findings.append(finding)
                        state.findings.append(finding)
            
            step.status = "completed"
            state.progress_log.append(f"[{datetime.now().isoformat()}] Found {len(step.findings)} sources for: {step.topic}")
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        state.iteration_count += 1
        return state
    
    # ========================================================================
    # NODE C: THE REVIEWER (Quality Control)
    # ========================================================================
    
    async def _node_reviewer(self, state: ResearchState) -> ResearchState:
        """
        Filter and classify findings for quality and relevance
        """
        state.status = "reviewing"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Reviewing {len(state.findings)} findings...")
        
        # Prepare findings for review
        findings_text = ""
        for i, f in enumerate(state.findings[:30]):  # Limit to 30 for context window
            findings_text += f"\n[{i+1}] Title: {f.title}\nSource: {f.source}\nContent: {f.raw_content[:500]}...\n"
        
        system_prompt = """You are the Scientific Reviewer for PharmGPT. You have received raw search results. Your job is to filter them for quality and relevance.

**Instructions:**
1. **Relevance Filter:** Discard results that are irrelevant or from non-reputable sources.
2. **Study Classification:** For each valid result, classify the study type:
   - *In Silico* (Docking/AI)
   - *In Vitro* (Cell lines)
   - *In Vivo* (Animal models)
   - *Clinical* (Human trials - Phase I/II/III)
   - *Review* (Literature review)
3. **Key Finding Extraction:** Extract the core Result/Conclusion from the text.

**Output Format (JSON Array):**
[
  {
    "index": 1,
    "relevant": true,
    "study_type": "In Vivo (Murine)",
    "key_finding": "Compound X reduced tumor volume by 40% (p<0.05).",
    "data_limitation": "Abstract Only; specific dosage not listed."
  }
]"""

        user_prompt = f"Research Question: {state.research_question}\n\nRaw Findings:\n{findings_text}"
        
        response = await self._call_llm(system_prompt, user_prompt, json_mode=True)
        
        try:
            reviews = json.loads(response)
            
            # Update findings with review data
            citation_id = 1
            for review in reviews:
                idx = review.get("index", 0) - 1
                if 0 <= idx < len(state.findings) and review.get("relevant", False):
                    finding = state.findings[idx]
                    finding.study_type = review.get("study_type", "")
                    finding.key_finding = review.get("key_finding", "")
                    finding.data_limitation = review.get("data_limitation", "")
                    
                    # Create citation with full metadata
                    # Try to find the original PubMed data for author/year info
                    pubmed_data = None
                    for f in state.findings:
                        if f.title == finding.title and hasattr(f, '_pubmed_data'):
                            pubmed_data = f._pubmed_data
                            break
                    
                    citation = Citation(
                        id=citation_id,
                        title=finding.title,
                        authors=pubmed_data.get("authors", "") if pubmed_data else "",
                        source=pubmed_data.get("journal", finding.source) if pubmed_data else finding.source,
                        url=finding.url,
                        doi=pubmed_data.get("doi", "") if pubmed_data else None,
                        pmid=pubmed_data.get("pmid", "") if pubmed_data else None,
                        year=pubmed_data.get("year", "") if pubmed_data else None,
                        data_limitation=finding.data_limitation
                    )
                    state.citations.append(citation)
                    citation_id += 1
            
            state.progress_log.append(f"[{datetime.now().isoformat()}] Validated {len(state.citations)} citations")
            
        except json.JSONDecodeError as e:
            state.progress_log.append(f"[{datetime.now().isoformat()}] Review parsing error: {e}")
        
        return state

    # ========================================================================
    # NODE D: THE WRITER (Medical Writer)
    # ========================================================================
    
    async def _node_writer(self, state: ResearchState) -> ResearchState:
        """
        Synthesize findings into a professional research report with APA 7th edition citations
        """
        state.status = "writing"
        state.progress_log.append(f"[{datetime.now().isoformat()}] Synthesizing final report...")
        
        # Prepare validated findings with full metadata
        findings_text = ""
        for i, citation in enumerate(state.citations[:20]):
            finding = next((f for f in state.findings if f.title == citation.title), None)
            if finding:
                findings_text += f"\n[{citation.id}] {citation.title}\n"
                findings_text += f"   Authors: {citation.authors or 'Unknown'}\n"
                findings_text += f"   Year: {citation.year or 'n.d.'}\n"
                findings_text += f"   Source: {citation.source} | URL: {citation.url}\n"
                if citation.doi:
                    findings_text += f"   DOI: {citation.doi}\n"
                findings_text += f"   Study Type: {finding.study_type or 'N/A'}\n"
                findings_text += f"   Key Finding: {finding.key_finding}\n"
                if finding.data_limitation:
                    findings_text += f"   Limitation: {finding.data_limitation}\n"
        
        # Prepare APA 7th edition references
        references_text = ""
        for citation in state.citations[:20]:
            # APA 7th format: Author, A. A., & Author, B. B. (Year). Title. Journal. DOI/URL
            authors = citation.authors if citation.authors else "Unknown Author"
            year = citation.year if citation.year else "n.d."
            doi_url = f"https://doi.org/{citation.doi}" if citation.doi else citation.url
            references_text += f"[{citation.id}] {authors} ({year}). {citation.title}. *{citation.source}*. {doi_url}\n"
        
        system_prompt = """You are the Senior Medical Writer for PharmGPT. Synthesize the research into a professional report following Nature Reviews style with APA 7th edition citations.

**Writing Guidelines:**

1. **Structure:**
   - **Executive Summary:** High-level answer (2-3 sentences).
   - **Detailed Analysis:** Group findings by theme (Mechanism, Efficacy, Safety, Clinical Evidence).
   - **Methodology Note:** State this report is based on PubMed/web data with limitations noted.
   - **References:** APA 7th edition formatted list.

2. **Inline Citation Style (APA 7th):**
   - Use narrative citations: "Smith et al. (2020) demonstrated that..."
   - Use parenthetical citations: "...showed significant efficacy (Jones & Lee, 2019)."
   - For direct findings: "Drug X reduced tumor volume by 40% (Chen et al., 2021)."
   - Multiple sources: "(Smith, 2020; Jones, 2019)"
   - **CRITICAL:** Only cite papers from the Validated Findings. DO NOT HALLUCINATE citations.

3. **Data Limitations:**
   - If marked `[Abstract Only]`, state: "Specific values were not available in the abstract (Author, Year)."
   - Clearly distinguish preclinical (in vitro/in vivo) from clinical (human) data.

4. **Tone:**
   - Objective, clinical, precise.
   - Use hedging language appropriately: "suggests", "indicates", "may".

5. **Reference List Format (APA 7th):**
   Author, A. A., Author, B. B., & Author, C. C. (Year). Title of article. *Journal Name*, Volume(Issue), Pages. https://doi.org/xxxxx

**Output:**
Return a well-structured Markdown report with proper APA inline citations and a References section."""

        user_prompt = f"""Research Question: {state.research_question}

Plan Overview: {state.plan_overview}

Validated Findings (use these for citations):
{findings_text}

Reference Data (APA format):
{references_text}

Synthesize a comprehensive research report with proper APA 7th edition citations."""

        response = await self._call_llm(system_prompt, user_prompt, json_mode=False)
        
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
            state = await self._node_planner(state)
            if state.error_message:
                state.status = "error"
                return state
            
            # Node B: Researching
            state = await self._node_researcher(state)
            
            # Node C: Reviewing
            state = await self._node_reviewer(state)
            
            # Node D: Writing
            state = await self._node_writer(state)
            
        except Exception as e:
            state.status = "error"
            state.error_message = str(e)
            state.progress_log.append(f"[{datetime.now().isoformat()}] ERROR: {e}")
        
        return state
    
    async def run_research_streaming(self, question: str, user_id: UUID):
        """
        Execute deep research with streaming progress updates
        Yields JSON progress updates
        """
        state = ResearchState(research_question=question)
        
        yield json.dumps({
            "type": "status",
            "status": "initializing",
            "message": "Starting deep research...",
            "progress": 0
        }) + "\n"
        
        try:
            # Node A: Planning
            yield json.dumps({
                "type": "status",
                "status": "planning",
                "message": "Analyzing query and creating research plan...",
                "progress": 10
            }) + "\n"
            
            state = await self._node_planner(state)
            
            if state.error_message:
                yield json.dumps({
                    "type": "error",
                    "message": state.error_message
                }) + "\n"
                return
            
            yield json.dumps({
                "type": "plan",
                "plan_overview": state.plan_overview,
                "steps": [{"id": s.id, "topic": s.topic, "source": s.source_preference} for s in state.steps],
                "progress": 20
            }) + "\n"
            
            # Node B: Researching
            yield json.dumps({
                "type": "status",
                "status": "researching",
                "message": f"Searching {len(state.steps)} research topics...",
                "progress": 30
            }) + "\n"
            
            state = await self._node_researcher(state)
            
            yield json.dumps({
                "type": "findings",
                "count": len(state.findings),
                "message": f"Found {len(state.findings)} relevant sources",
                "progress": 60
            }) + "\n"
            
            # Node C: Reviewing
            yield json.dumps({
                "type": "status",
                "status": "reviewing",
                "message": "Analyzing and validating sources...",
                "progress": 70
            }) + "\n"
            
            state = await self._node_reviewer(state)
            
            yield json.dumps({
                "type": "citations",
                "count": len(state.citations),
                "message": f"Validated {len(state.citations)} citations",
                "progress": 80
            }) + "\n"
            
            # Node D: Writing
            yield json.dumps({
                "type": "status",
                "status": "writing",
                "message": "Synthesizing research report...",
                "progress": 90
            }) + "\n"
            
            state = await self._node_writer(state)
            
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
                        "authors": c.authors or "",
                        "year": c.year or "",
                        "journal": c.source if c.source != "Web" else "",
                        "doi": c.doi or ""
                    }
                    for c in state.citations
                ],
                "progress": 100
            }) + "\n"
            
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e)
            }) + "\n"
