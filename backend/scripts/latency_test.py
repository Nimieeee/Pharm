
import asyncio
import time
import os
import httpx
from app.core.config import settings
from app.services.tools import BiomedicalTools

# We need to initialize things manually to avoid full app startup overhead
import sys
# sys.path.append(os.getcwd())

async def measure_latency():
    print("🚀 Starting Latency Diagnostics...")
    
    # 1. External API (OpenFDA)
    print("\n--- 1. External Tools (OpenFDA) ---")
    tools = BiomedicalTools()
    start = time.time()
    await tools.fetch_openfda_label("clozapine")
    fda_time = time.time() - start
    print(f"✅ OpenFDA Fetch: {fda_time:.4f}s")
    
    # 2. Embedding Generation (Mistral)
    print("\n--- 2. Embedding Generation ---")
    try:
        from app.services.mistral_embeddings import get_mistral_embeddings_service
        embed_service = get_mistral_embeddings_service()
        start = time.time()
        await embed_service.generate_embedding("Test query for latency")
        embed_time = time.time() - start
        print(f"✅ Mistral Embedding: {embed_time:.4f}s")
    except Exception as e:
        print(f"❌ Embedding Error: {e}")

    # 3. LLM Generation (NVIDIA NIM vs Mistral)
    print("\n--- 3. LLM Generation ---")
    
    if settings.NVIDIA_API_KEY:
        print(f"Testing NVIDIA NIM ({settings.NVIDIA_MODEL})...")
        start = time.time()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://integrate.api.nvidia.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.NVIDIA_API_KEY}"},
                json={
                    "model": "moonshotai/kimi-k2.5",
                    "messages": [{"role": "user", "content": "Hello, say hi."}],
                    "max_tokens": 10
                },
                timeout=30
            )
        nvidia_time = time.time() - start
        print(f"✅ NVIDIA NIM: {nvidia_time:.4f}s (Status: {resp.status_code})")
    
    if settings.MISTRAL_API_KEY:
        print(f"Testing Mistral (mistral-small-latest)...")
        start = time.time()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.MISTRAL_API_KEY}"},
                json={
                    "model": "mistral-small-latest",
                    "messages": [{"role": "user", "content": "Hello, say hi."}],
                    "max_tokens": 10
                },
                timeout=30
            )
        mistral_time = time.time() - start
        print(f"✅ Mistral API: {mistral_time:.4f}s (Status: {resp.status_code})")

if __name__ == "__main__":
    asyncio.run(measure_latency())
