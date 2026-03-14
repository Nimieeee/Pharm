
import json
import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Mock EVERYTHING before importing SlideService to avoid dependency issues
sys.modules['pptx'] = MagicMock()
sys.modules['pptx.util'] = MagicMock()
sys.modules['pptx.enum.dml'] = MagicMock()
sys.modules['pptx.enum.text'] = MagicMock()
sys.modules['pptx.dml.color'] = MagicMock()

# Bypass pydantic settings
os.environ["SUPABASE_URL"] = "https://mock.supabase.co"
os.environ["SUPABASE_ANON_KEY"] = "mock_key"
os.environ["MISTRAL_API_KEY"] = "mock_key"
os.environ["NVIDIA_API_KEY"] = "mock_key"
os.environ["GROQ_API_KEY"] = "mock_key"

# Now we can import
from app.services.slide_service import SlideService

async def test_json_extraction():
    # Mock dependencies
    mock_ai = MagicMock()
    mock_image_gen = MagicMock()
    
    # Mock the design engine 
    mock_design = MagicMock()
    mock_design.analyze_and_adjust = lambda x: x
    
    service = SlideService(mock_ai, mock_image_gen)
    service.design = mock_design
    
    test_cases = [
        {
            "name": "Clean JSON",
            "response": '{"title": "Test", "slides": []}',
            "should_pass": True
        },
        {
            "name": "Markdown Wrapped",
            "response": '```json\n{"title": "Test", "slides": []}\n```',
            "should_pass": True
        },
        {
            "name": "Markdown with Text",
            "response": 'Here is the outline:\n```json\n{"title": "Test", "slides": []}\n```\nHope you like it!',
            "should_pass": True
        },
        {
            "name": "Loose Object in Text",
            "response": 'The presentation is ready: {"title": "Test", "slides": []} and it looks great.',
            "should_pass": True
        },
        {
            "name": "Malformed (Empty)",
            "response": '',
            "should_pass": False
        },
        {
            "name": "Malformed (No JSON)",
            "response": 'I am sorry, I cannot generate that for you.',
            "should_pass": False
        }
    ]
    
    print("\n--- Testing SlideService JSON Extraction ---\n")
    
    for case in test_cases:
        mock_ai.generate = AsyncMock(return_value=case["response"])
        
        try:
            # We don't care about the result, just if it parses
            await service.generate_outline("topic")
            success = True
        except Exception as e:
            success = False
            error = str(e)
            
        if success == case["should_pass"]:
            print(f"✅ PASS: {case['name']}")
        else:
            status = "Succeeded" if success else "Failed"
            print(f"❌ FAIL: {case['name']} (Expected {case['should_pass']}, but {status})")
            if not success:
                print(f"   Error: {error}")

if __name__ == "__main__":
    asyncio.run(test_json_extraction())
