import asyncio
import httpx
import os

# Set the key provided by the user
SERP_API_KEY = "6e95deed5139330fe2d1234c896b363a679ee0a5f4e6db44ff04af550300df2e"

async def verify_serp():
    print(f"Testing SERP API Key: {SERP_API_KEY[:5]}...{SERP_API_KEY[-5:]}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("Sending request to Google Scholar via SERP API...")
            response = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_scholar",
                    "q": "Parkinson's disease",
                    "api_key": SERP_API_KEY,
                    "num": 1,
                    "hl": "en"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "error" in data:
                    print(f"❌ API Error: {data['error']}")
                else:
                    results = data.get("organic_results", [])
                    print(f"✅ Success! Found {len(results)} results.")
                    if results:
                        first = results[0]
                        print(f"Sample Title: {first.get('title')}")
                        print(f"Sample Link: {first.get('link')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(verify_serp())
