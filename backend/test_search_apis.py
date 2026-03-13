"""
Test script to verify search APIs (Tavily, SERP, PubMed) are working correctly
"""
import asyncio
import os
from app.services.deep_research import ResearchTools

async def test_search_apis():
    tools = ResearchTools()
    
    print("=" * 80)
    print("TESTING SEARCH APIs")
    print("=" * 80)
    
    # Test query
    query = "metformin mechanism of action"
    
    # Check API keys
    print("\n📋 API Key Status:")
    print(f"  Tavily API Key: {'✅ Configured' if tools.tavily_api_key else '❌ Missing'}")
    print(f"  SERP API Key: {'✅ Configured' if tools.serp_api_key else '❌ Missing'}")
    print(f"  Serper API Key: {'✅ Configured' if tools.serper_api_key else '❌ Missing'}")
    
    # Test PubMed
    print(f"\n\n🔬 Testing PubMed API with query: '{query}'")
    print("-" * 80)
    try:
        pubmed_results = await tools.search_pubmed(query, max_results=3)
        print(f"✅ PubMed returned {len(pubmed_results)} results")
        for i, r in enumerate(pubmed_results, 1):
            print(f"\n  [{i}] {r.get('title', 'No title')}")
            print(f"      PMID: {r.get('pmid', 'N/A')}")
            print(f"      DOI: {r.get('doi', 'N/A')}")
            print(f"      Authors: {r.get('authors', 'N/A')[:50]}...")
            print(f"      Year: {r.get('year', 'N/A')}")
            print(f"      Journal: {r.get('journal', 'N/A')[:50]}...")
            print(f"      URL: {r.get('url', 'N/A')}")
            print(f"      Abstract: {r.get('abstract', 'N/A')[:100]}...")
    except Exception as e:
        print(f"❌ PubMed Error: {e}")
    
    # Test Tavily
    print(f"\n\n🌐 Testing Tavily API with query: '{query}'")
    print("-" * 80)
    try:
        tavily_results = await tools.search_web(query, max_results=3)
        print(f"✅ Tavily returned {len(tavily_results)} results")
        for i, r in enumerate(tavily_results, 1):
            print(f"\n  [{i}] {r.get('title', 'No title')}")
            print(f"      URL: {r.get('url', 'N/A')}")
            print(f"      Source: {r.get('source', 'N/A')}")
            print(f"      Snippet: {r.get('snippet', 'N/A')[:100]}...")
    except Exception as e:
        print(f"❌ Tavily Error: {e}")
    
    # Test Google Scholar (SERP API)
    print(f"\n\n🎓 Testing Google Scholar (SERP API) with query: '{query}'")
    print("-" * 80)
    try:
        scholar_results = await tools.search_google_scholar(query, max_results=3)
        print(f"✅ Google Scholar returned {len(scholar_results)} results")
        for i, r in enumerate(scholar_results, 1):
            print(f"\n  [{i}] {r.get('title', 'No title')}")
            print(f"      Authors: {r.get('authors', 'N/A')}")
            print(f"      Year: {r.get('year', 'N/A')}")
            print(f"      Journal: {r.get('journal', 'N/A')}")
            print(f"      Cited by: {r.get('cited_by', 0)}")
            print(f"      URL: {r.get('url', 'N/A')}")
            print(f"      PDF: {r.get('pdf_url', 'N/A')}")
            print(f"      Snippet: {r.get('snippet', 'N/A')[:100]}...")
    except Exception as e:
        print(f"❌ Google Scholar Error: {e}")
    
    # Test DuckDuckGo
    print(f"\n\n🦆 Testing DuckDuckGo with query: '{query}'")
    print("-" * 80)
    try:
        ddg_results = await tools.search_duckduckgo(query, max_results=3)
        print(f"✅ DuckDuckGo returned {len(ddg_results)} results")
        for i, r in enumerate(ddg_results, 1):
            print(f"\n  [{i}] {r.get('title', 'No title')}")
            print(f"      URL: {r.get('url', 'N/A')}")
            print(f"      Snippet: {r.get('snippet', 'N/A')[:100]}...")
    except Exception as e:
        print(f"❌ DuckDuckGo Error: {e}")
    
    # Test Serper
    print(f"\n\n🔍 Testing Serper API with query: '{query}'")
    print("-" * 80)
    try:
        serper_results = await tools.search_serper(query, max_results=3)
        print(f"✅ Serper returned {len(serper_results)} results")
        for i, r in enumerate(serper_results, 1):
            print(f"\n  [{i}] {r.get('title', 'No title')}")
            print(f"      URL: {r.get('url', 'N/A')}")
            print(f"      Snippet: {r.get('snippet', 'N/A')[:100]}...")
    except Exception as e:
        print(f"❌ Serper Error: {e}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_search_apis())
