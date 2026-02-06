import asyncio
import httpx
import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.core.config import settings

async def test_kimi():
    print(f"Testing Kimi with API Key: {settings.NVIDIA_API_KEY[:5]}...{settings.NVIDIA_API_KEY[-5:] if settings.NVIDIA_API_KEY else 'None'}")
    
    messages = [
        {"role": "system", "content": "You are a translator. Translate to Spanish."},
        {"role": "user", "content": "Hello world"}
    ]
    
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "moonshotai/kimi-k2.5",
        "messages": messages,
        "temperature": 0.1
    }
    
    print(f"Sending request to {url}...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("Success!")
                print(response.json()['choices'][0]['message']['content'])
            else:
                print(f"Error Body: {response.text}")
    except Exception as e:
        print(f"Exception: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_kimi())
