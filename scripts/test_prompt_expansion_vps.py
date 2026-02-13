
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend directory to sys.path
sys.path.append("/var/www/pharmgpt-backend/backend")

# Load environment variables
load_dotenv("/var/www/pharmgpt-backend/backend/.env")

# Mock the database client
class MockDB:
    def __init__(self):
        pass

# Mock dependencies
import app.services.ai
app.services.ai.Client = MockDB  # Patch typing if needed, simplistic mock

from app.services.ai import AIService

# Patch dependencies in __init__ to avoid needing real DB
# We can just instantiate it with a mock and hope it doesn't crash on init
# The init does:
# self.db = db
# self.rag_service = EnhancedRAGService(db) -> this might be tricky
# self.chat_service = ChatService(db)
# ...

# Better approach: Instantiate AIService then fix its internal state if it crashes, 
# or mock the imported classes.

from unittest.mock import MagicMock

# Mock the services that require DB
app.services.ai.EnhancedRAGService = MagicMock()
app.services.ai.ChatService = MagicMock()
app.services.ai.BiomedicalTools = MagicMock()
app.services.ai.PlottingService = MagicMock()
app.services.ai.ImageGenerationService = MagicMock()

async def test_expansion():
    print("🚀 Initializing AIService...")
    try:
        service = AIService(MagicMock())
        print(f"✅ Service initialized. Mistral API Key present: {bool(service.mistral_api_key)}")
        
        prompt = "A baby with spina bifida"
        print(f"\n📝 Testing prompt: '{prompt}'")
        
        enhanced = await service.enhance_image_prompt(prompt)
        print(f"\n✨ Enhanced Prompt:\n{enhanced}")
        
        if enhanced == prompt:
            print("\n❌ Expansion failed (returned original). Check API key or connection.")
        else:
            print("\n✅ Expansion successful!")
            
            # Now download the image to verify visual quality
            import httpx
            import urllib.parse
            
            print("\n⬇️ Downloading image verification...")
            encoded_prompt = urllib.parse.quote(enhanced)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&width=1024&height=1024"
            print(f"URL: {url}")
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=30.0)
                if resp.status_code == 200:
                    output_path = "/var/www/pharmgpt-backend/backend/test_result_baby.jpg"
                    with open(output_path, "wb") as f:
                        f.write(resp.content)
                    print(f"✅ Image saved to {output_path}")
                else:
                    print(f"❌ Failed to download image: {resp.status_code}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_expansion())
