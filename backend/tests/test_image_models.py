import asyncio
import httpx
import os
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend or root
load_dotenv("backend/.env")
load_dotenv(".env")

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
OUTPUT_DIR = Path("backend/tests/image_model_comparison")
PROMPT = "well labelled diagram of spina bifida"

MODELS = [
    "flux",
    "zimage",
    "imagen-4",
    "grok-imagine",
    "klein",
    "klein-large"
]

async def test_model(model: str):
    print(f"Testing model: {model}...")
    
    # Apply scientific style keywords similar to image_gen.py
    style_keywords = "medical textbook diagram, anatomically correct cross-section, correct physiological structure, clearly labeled parts, proper spelling, legible annotations, schematic, educational infographic, high detail, white background, vector style, clean lines"
    final_prompt = f"{PROMPT}, {style_keywords}"
    
    encoded_prompt = urllib.parse.quote(final_prompt, safe='')
    url = f"https://gen.pollinations.ai/image/{encoded_prompt}"
    
    params = {
        "model": model,
        "width": 1024,
        "height": 1024,
        "nologo": "true",
        "safe": "true",
        "seed": 42
    }
    
    headers = {}
    if POLLINATIONS_API_KEY and POLLINATIONS_API_KEY.strip():
        headers["Authorization"] = f"Bearer {POLLINATIONS_API_KEY}"
    
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                output_path = OUTPUT_DIR / f"{model}.png"
                output_path.write_bytes(resp.content)
                print(f"✅ Success: Saved to {output_path}")
            elif resp.status_code == 401:
                print(f"❌ UNAUTHORIZED for {model}: Requires API Key")
            else:
                print(f"❌ Error {resp.status_code} for {model}: {resp.text}")
    except Exception as e:
        print(f"❌ Exception for {model}: {e}")

async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    tasks = [test_model(model) for model in MODELS]
    await asyncio.gather(*tasks)
    print("\nComparison complete. Check backend/tests/image_model_comparison/")

if __name__ == "__main__":
    asyncio.run(main())
