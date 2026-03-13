"""
Test Kimi K2.5 for normal chat (mimics AIService._stream_nvidia_kimi)
"""
import asyncio
import httpx
import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.core.config import settings

async def test_kimi_chat():
    """Test Kimi K2.5 streaming response like AIService does"""
    
    NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
    NVIDIA_MODEL = "moonshotai/kimi-k2.5"
    
    print(f"Testing Kimi Chat with:")
    print(f"  URL: {NVIDIA_BASE_URL}")
    print(f"  Model: {NVIDIA_MODEL}")
    print(f"  API Key: {settings.NVIDIA_API_KEY[:10]}...{settings.NVIDIA_API_KEY[-5:]}")
    
    messages = [
        {"role": "system", "content": "You are a helpful pharmacology assistant."},
        {"role": "user", "content": "What is aspirin?"}
    ]
    
    headers = {
        "Authorization": f"Bearer {settings.NVIDIA_API_KEY}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": NVIDIA_MODEL,
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.7,
        "top_p": 1.0,
        "stream": True
    }
    
    print("\n🚀 Sending streaming request...")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                NVIDIA_BASE_URL,
                headers=headers,
                json=payload
            ) as response:
                print(f"📡 Response Status: {response.status_code}")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"❌ Error: {error_text.decode()}")
                    return
                
                print("✅ Streaming response:\n")
                full_response = ""
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if chunk.get("choices") and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    print(content, end="", flush=True)
                                    full_response += content
                        except json.JSONDecodeError:
                            continue
                
                print(f"\n\n✅ Total response length: {len(full_response)} chars")
                
    except httpx.TimeoutException as e:
        print(f"❌ TIMEOUT: {e}")
        print("The VPS cannot reach NVIDIA API within 120 seconds")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_kimi_chat())
