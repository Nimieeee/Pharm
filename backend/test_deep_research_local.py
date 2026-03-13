import asyncio
import os
import sys
from pprint import pprint
from dotenv import load_dotenv

load_dotenv()

# Provide dummy env vars if missing to pass pydantic validation
if not os.environ.get("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "http://localhost:8000"
if not os.environ.get("SUPABASE_ANON_KEY"):
    os.environ["SUPABASE_ANON_KEY"] = "dummy"

# Set up path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.deep_research import DeepResearchService
from supabase import create_client

async def run_test():
    print("Testing Deep Research Pipeline...")
    
    # Needs a real DB client or mock depending on DeepResearchAgent implementation
    # It seems to just need `db` for some progress logging if at all
    # DeepResearchService doesn't strictly depend on the db for running the research itself
    # but let's provide a mock db if possible or real one
    
    # Initialize real sb client if env vars are present
    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    db = None
    if supabase_url and supabase_key and supabase_url != "http://localhost:8000":
        try:
            db = create_client(supabase_url, supabase_key)
        except:
            pass
        
    agent = DeepResearchService(db=db)
    
    query = "Compare FDA vs EMA approval processes for new molecular entities"
    print(f"Query: {query}")
    
    try:
        report_state = await agent.run_research(query, user_id="test_user")
        # Display result using the accessor method
        print("\n--- TEST COMPLETE ---")
        print(f"Report length: {len(report_state.final_report)} chars")
        print(f"Total citations used: {len(report_state.citations)}")
        
        print("\n=== Citation Source Breakdown ===")
        from collections import Counter
        source_counts = Counter()
        for c in report_state.citations[:20]:
            # 'c.source' contains the journal if PubMed, else 'Web' or Google Scholar sources.
            # But we actually want to know the API source. 
            # In deep_research.py, f.source is the raw domain/tool name.
            # Wait, c.source is overwritten with journal name if from PubMed!
            # If c.pmid exists, it's from PubMed!
            if getattr(c, 'pmid', None):
                source_counts["PubMed API"] += 1
            elif getattr(c, 'url', "") and "scholar.google" in getattr(c, 'url', ""):
                source_counts["Google Scholar"] += 1
            else:
                source_counts["Tavily/SERP Web"] += 1
                
        print(f"| Source | Count |")
        print(f"|---|---|")
        for s, counts in source_counts.items():
            print(f"| {s} | {counts} |")
            
        print("\n=== Final Report Snippet ===")
        print(report_state.final_report[:500] + "...\n\n[TRUNCATED]\n\n..." + report_state.final_report[-2000:])
        
        # Save the full string to a file to verify output
        with open("test_report_output.md", "w") as f:
            f.write(report_state.final_report)
        
        print("\nReport saved to test_report_output.md")
    except Exception as e:
        print(f"Error during research: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(run_test())
