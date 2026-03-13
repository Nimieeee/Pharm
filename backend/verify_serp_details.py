import asyncio
import httpx
import json

# Set the key provided by the user
SERP_API_KEY = "6e95deed5139330fe2d1234c896b363a679ee0a5f4e6db44ff04af550300df2e"

async def verify_serp_details():
    print(f"Testing SERP API Details...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_scholar",
                    "q": "Parkinson's disease treatment",
                    "api_key": SERP_API_KEY,
                    "num": 1,
                    "hl": "en"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("organic_results", [])
                if results:
                    first = results[0]
                    print("\n--- Raw Result Data ---")
                    print(json.dumps(first.get("publication_info"), indent=2))
                    print("\n--- Extracted Fields ---")
                    print(f"Title: {first.get('title')}")
                    print(f"Snippet: {first.get('snippet')[:50]}...")
                    
                    pub_info = first.get("publication_info", {})
                    summary = pub_info.get("summary", "")
                    print(f"Summary String: '{summary}'")
                    
                    # Test extraction logic
                    authors_list = pub_info.get("authors", [])
                    authors = ", ".join([a.get("name", "") for a in authors_list])
                    print(f"Authors: {authors}")
                    
                    # Try to parse journal/year from summary
                    # Format usually: "Authors - Journal, Year - Publisher"
                    parts = summary.split(" - ")
                    if len(parts) >= 2:
                        # Middle part often contains Journal, Year
                        # e.g. "Nature, 2020"
                        journal_year = parts[1]
                        print(f"Potential Journal/Year part: '{journal_year}'")
                    
            else:
                print(f"Error: {response.status_code}")
                
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(verify_serp_details())
