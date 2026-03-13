"""
Serper API Service for Reference Sourcing
Provides access to Google Scholar, News, Patents for lab report references
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SerperResult:
    """A single search result from Serper."""
    title: str
    link: str
    snippet: str
    source: str  # 'scholar', 'news', 'patents'
    authors: Optional[str] = None
    year: Optional[str] = None
    cited_by: Optional[int] = None


class SerperService:
    """
    Service for searching Google Scholar, News, and Patents via Serper API.
    Used for finding real references for lab reports.
    """
    
    def __init__(self):
        self.api_key = getattr(settings, 'SERPER_API_KEY', None) or "5806f48daa69f0c91308edc29e6d166bf3269b03"
        self.base_urls = {
            "scholar": "https://google.serper.dev/scholar",
            "news": "https://google.serper.dev/news",
            "patents": "https://google.serper.dev/patents",
            "search": "https://google.serper.dev/search",
            "scrape": "https://scrape.serper.dev"
        }
    
    async def search_scholar(
        self, 
        query: str, 
        num_results: int = 10
    ) -> List[SerperResult]:
        """
        Search Google Scholar for academic papers.
        
        Args:
            query: Search query (e.g., "therapeutic index LD50 ED50")
            num_results: Number of results to return
            
        Returns:
            List of SerperResult objects with citation information
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_urls["scholar"],
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "num": num_results
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Serper Scholar error: {response.status_code} - {response.text}")
                    return []
                
                data = response.json()
                results = []
                
                for item in data.get("organic", [])[:num_results]:
                    results.append(SerperResult(
                        title=item.get("title", ""),
                        link=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source="scholar",
                        authors=item.get("publication_info", {}).get("authors", ""),
                        year=item.get("year", ""),
                        cited_by=item.get("inline_links", {}).get("cited_by", {}).get("total", 0)
                    ))
                
                logger.info(f"📚 Serper Scholar: Found {len(results)} results for '{query}'")
                return results
                
        except Exception as e:
            logger.error(f"Serper Scholar search failed: {e}")
            return []
    
    async def search_news(
        self, 
        query: str, 
        num_results: int = 5
    ) -> List[SerperResult]:
        """
        Search Google News for recent articles.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SerperResult objects with news articles
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_urls["news"],
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "num": num_results
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Serper News error: {response.status_code}")
                    return []
                
                data = response.json()
                results = []
                
                for item in data.get("news", [])[:num_results]:
                    results.append(SerperResult(
                        title=item.get("title", ""),
                        link=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source="news",
                        authors=item.get("source", "")
                    ))
                
                logger.info(f"📰 Serper News: Found {len(results)} results for '{query}'")
                return results
                
        except Exception as e:
            logger.error(f"Serper News search failed: {e}")
            return []
    
    async def search_patents(
        self, 
        query: str, 
        num_results: int = 5
    ) -> List[SerperResult]:
        """
        Search Google Patents.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of SerperResult objects with patent information
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_urls["patents"],
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "q": query,
                        "num": num_results
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Serper Patents error: {response.status_code}")
                    return []
                
                data = response.json()
                results = []
                
                for item in data.get("organic", [])[:num_results]:
                    results.append(SerperResult(
                        title=item.get("title", ""),
                        link=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source="patents"
                    ))
                
                logger.info(f"📜 Serper Patents: Found {len(results)} results for '{query}'")
                return results
                
        except Exception as e:
            logger.error(f"Serper Patents search failed: {e}")
            return []
    
    async def get_references_for_topic(
        self, 
        topic: str, 
        include_scholar: bool = True,
        include_news: bool = False,
        include_patents: bool = False,
        max_total: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get references from multiple sources for a topic.
        
        Args:
            topic: The research topic
            include_scholar: Include Google Scholar results
            include_news: Include News results
            include_patents: Include Patent results
            max_total: Maximum total references to return
            
        Returns:
            List of formatted reference dictionaries
        """
        all_results: List[SerperResult] = []
        
        if include_scholar:
            scholar_results = await self.search_scholar(topic, num_results=max_total)
            all_results.extend(scholar_results)
        
        if include_news:
            news_results = await self.search_news(topic, num_results=3)
            all_results.extend(news_results)
        
        if include_patents:
            patent_results = await self.search_patents(topic, num_results=2)
            all_results.extend(patent_results)
        
        # Format as references
        references = []
        for result in all_results[:max_total]:
            ref = {
                "title": result.title,
                "url": result.link,
                "source_type": result.source,
                "snippet": result.snippet
            }
            
            if result.authors:
                ref["authors"] = result.authors
            if result.year:
                ref["year"] = result.year
            if result.cited_by:
                ref["cited_by"] = result.cited_by
            
            # Format as citation text
            if result.source == "scholar":
                author_part = result.authors.split(",")[0] if result.authors else "Unknown"
                year_part = f" ({result.year})" if result.year else ""
                ref["citation_text"] = f"{author_part} et al.{year_part}. {result.title}. {result.link}"
            else:
                ref["citation_text"] = f"{result.title}. {result.link}"
            
            references.append(ref)
        
        logger.info(f"📖 Total references gathered: {len(references)} for topic '{topic}'")
        return references
    
    async def scrape_page(self, url: str, include_markdown: bool = True) -> Optional[str]:
        """
        Scrape a webpage and return its content.
        
        Args:
            url: URL to scrape
            include_markdown: Return content as markdown
            
        Returns:
            Page content as text/markdown or None on error
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.base_urls["scrape"],
                    headers={
                        "X-API-KEY": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": url,
                        "includeMarkdown": include_markdown
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Serper Scrape error: {response.status_code}")
                    return None
                
                data = response.json()
                return data.get("markdown" if include_markdown else "text", "")
                
        except Exception as e:
            logger.error(f"Serper Scrape failed: {e}")
            return None
