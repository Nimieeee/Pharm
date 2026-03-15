import httpx
import json
import asyncio

BASE_URL = "http://localhost:7860/api/v1"

async def test_pdf_download():
    print("\n--- Testing PDF Download (Restricted DOI) ---")
    doi = "10.1002/cbic.202300816"
    url = f"{BASE_URL}/literature/pdf/download?doi={doi}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Mocking user login is not needed for localhost if security is bypassed or internal
        # But for completeness, we can try without auth first or assume dev mode
        try:
            resp = await client.get(url)
            print(f"Status: {resp.status_code}")
            print(f"Detail: {resp.text}")
            if resp.status_code == 403:
                print("✅ Successfully handled restricted PDF with 403")
            elif resp.status_code == 200:
                print("✅ PDF downloaded successfully (maybe OA now?)")
            else:
                print(f"❌ Unexpected status code: {resp.status_code}")
        except Exception as e:
            print(f"❌ Request failed: {e}")

async def test_slide_outline():
    print("\n--- Testing Slide Outline (Detailed Mode) ---")
    url = f"{BASE_URL}/slides/outline"
    payload = {
        "topic": "Metformin in PD research",
        "num_slides": 12,
        "theme": "ocean_gradient"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(url, json=payload)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ Successfully generated outline for {len(data['slides'])} slides")
                print("✅ JSON is valid")
            else:
                print(f"❌ Failed to generate outline: {resp.text}")
        except Exception as e:
            print(f"❌ Request failed: {e}")

async def main():
    # Note: These might fail if security dependency is strictly enforced on localhost
    # But usually API endpoints on VPS for testing can be called
    await test_pdf_download()
    await test_slide_outline()

if __name__ == "__main__":
    asyncio.run(main())
