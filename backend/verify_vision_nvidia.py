import sys
import os
import asyncio
import io
import logging
import time
from PIL import Image, ImageDraw

# Add current directory to path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_vision_direct():
    print("🚀 Starting Direct Vision Service Test (NVIDIA Integration)...")
    
    # Import the service (this will fail if dependencies are missing, ensuring we test the env)
    from app.services.vision_service import process_visual_document, NVIDIA_API_URL
    
    print(f"✅ Service imported. Targeted API URL in code: {NVIDIA_API_URL}")
    
    # 1. Create a Dummy Image (A simple red square with text)
    print("🎨 Generating test image...")
    img = Image.new('RGB', (400, 400), color = 'white')
    d = ImageDraw.Draw(img)
    d.text((10,10), "This is a test of the NVIDIA Mistral Vision API.", fill=(0,0,0))
    d.rectangle([50, 50, 150, 150], fill="red")
    
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    msg_size = len(img_bytes) / 1024
    print(f"📦 Generated image ({msg_size:.2f} KB).")

    # 2. Call the Service
    print("⚡ Invoking process_visual_document...")
    start_time = time.time()
    
    # We use a dummy API key because the service now uses the hardcoded NVIDIA_KEY internally
    # but still expects an argument.
    result = await process_visual_document(
        content=img_bytes,
        filename="test_image.png",
        user_prompt="Describe this image.",
        api_key="dummy_key", 
        mode="fast"
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n⏱️ Processing Time: {duration:.2f}s")
    
    # 3. Validation
    if "Error" in result or "Failed" in result:
        print("❌ TEST FAILED.")
        print(f"Output: {result}")
    else:
        print("✅ TEST PASSED.")
        print("📝 Description Output:")
        print("--------------------------------------------------")
        print(result)
        print("--------------------------------------------------")
        
        # Heuristic check
        if "red" in result.lower() or "nvidia" in result.lower():
            print("✅ Content accuracy check passed (found 'red' or text).")
        else:
            print("⚠️ Content seems generic, but API worked.")

if __name__ == "__main__":
    asyncio.run(test_vision_direct())
