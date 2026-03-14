
import json
import re

def extract_json(response: str) -> dict:
    """Mock implementation of the new logic in SlideService.generate_outline"""
    json_str = response.strip()
    
    # Look for JSON block if it's wrapped in markdown
    if "```" in json_str:
        # Try to find content between ```json and ``` or just ``` and ```
        import re
        blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", json_str, re.DOTALL)
        if blocks:
            json_str = blocks[0]
        else:
            # Fallback: just strip the markers
            parts = json_str.split("```")
            if len(parts) > 1:
                json_str = parts[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
    
    # Final attempt: find the first { and last } to isolate the JSON object
    if not (json_str.strip().startswith("{") and json_str.strip().endswith("}")):
        import re
        match = re.search(r"(\{.*\})", json_str, re.DOTALL)
        if match:
            json_str = match.group(1)
            
    return json.loads(json_str)

def test_json_extraction():
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
        }
    ]
    
    print("\n--- Testing SlideService JSON Extraction Logic ---\n")
    
    for case in test_cases:
        try:
            result = extract_json(case["response"])
            success = True
        except Exception as e:
            success = False
            error = str(e)
            
        if success == case["should_pass"]:
            print(f"✅ PASS: {case['name']}")
        else:
            print(f"❌ FAIL: {case['name']} (Error: {error})")

if __name__ == "__main__":
    test_json_extraction()
