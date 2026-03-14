
import io
import os
import sys
from unittest.mock import MagicMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Bypass pydantic settings
os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "mock_key"
os.environ["MISTRAL_API_KEY"] = "mock_key"

from app.services.design_engine import DesignEngine

def test_reproduce_rid():
    engine = DesignEngine()
    
    # Mock outline
    outline = {
        "title": "Test Presentation",
        "theme": "ocean_gradient",
        "slides": [
            {
                "slide_number": 1,
                "layout": "title",
                "title": "Welcome",
                "subtitle": "Test Rid Error"
            },
            {
                "slide_number": 2,
                "layout": "bullets_only",
                "title": "Second Slide",
                "bullets": ["Point A", "Point B"]
            }
        ]
    }
    
    content = outline["slides"]
    # Mock a small 1x1 white pixel image
    pixel_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdcD\x01\x14\x00\x00\x00\x00IEND\xaeB`\x82'
    
    images = {
        0: pixel_bytes
    }
    
    theme = engine.get_theme("ocean_gradient")
    
    print("Starting PPTX assembly...")
    try:
        pptx_bytes = engine.assemble_pptx(outline, content, images, theme)
        print("✅ Success! No rid error.")
    except Exception as e:
        print(f"❌ Caught Expected/Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_reproduce_rid()
