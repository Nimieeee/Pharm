"""
Test Qwen3-VL-Embedding-8B via multiple HF API approaches
"""
import os
import requests
import json

HF_TOKEN = os.environ.get("HF_TOKEN", "")
MODEL_ID = "Qwen/Qwen3-VL-Embedding-8B"

def test_feature_extraction():
    """Test via feature-extraction pipeline endpoint"""
    url = f"https://router.huggingface.co/hf-inference/pipeline/feature-extraction/{MODEL_ID}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": "This is a test sentence."}
    
    print(f"--- Test 1: Feature Extraction Pipeline ---")
    print(f"URL: {url}")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], list):
                print(f"✅ Embedding dim: {len(data[0])}")
            elif isinstance(data[0], float):
                print(f"✅ Embedding dim: {len(data)}")
            else:
                print(f"Response: {str(data)[:200]}")
        elif isinstance(data, dict) and "error" in data:
            print(f"❌ Error: {data['error']}")
        else:
            print(f"Response type: {type(data)}, content: {str(data)[:200]}")
    except:
        print(f"Raw: {response.text[:300]}")

def test_dedicated_endpoint():
    """Test via dedicated inference endpoint format"""
    url = f"https://router.huggingface.co/hf-inference/models/{MODEL_ID}"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    payload = {"inputs": "This is a test sentence.", "options": {"wait_for_model": True}}
    
    print(f"\n--- Test 2: Models Endpoint ---")
    print(f"URL: {url}")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        if isinstance(data, dict) and "error" in data:
            print(f"❌ Error: {data['error']}")
        else:
            print(f"Response type: {type(data)}, content: {str(data)[:200]}")
    except:
        print(f"Raw: {response.text[:300]}")

def test_huggingface_hub():
    """Test via huggingface_hub library"""
    print(f"\n--- Test 3: huggingface_hub InferenceClient ---")
    try:
        from huggingface_hub import InferenceClient
        client = InferenceClient(token=HF_TOKEN)
        result = client.feature_extraction("This is a test sentence.", model=MODEL_ID)
        print(f"✅ Success! Result type: {type(result)}, shape: {result.shape if hasattr(result, 'shape') else len(result)}")
    except ImportError:
        print("⚠️ huggingface_hub not installed")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_text_embeddings_inference():
    """Test via TEI-compatible endpoint"""
    url = f"https://router.huggingface.co/hf-inference/models/{MODEL_ID}/v1/embeddings"
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}
    payload = {"input": "This is a test sentence.", "model": MODEL_ID}
    
    print(f"\n--- Test 4: TEI /v1/embeddings Endpoint ---")
    print(f"URL: {url}")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        if isinstance(data, dict):
            if "data" in data and len(data["data"]) > 0:
                emb = data["data"][0].get("embedding", [])
                print(f"✅ Embedding dim: {len(emb)}")
            elif "error" in data:
                print(f"❌ Error: {data['error']}")
            else:
                print(f"Response: {str(data)[:200]}")
        else:
            print(f"Response type: {type(data)}")
    except:
        print(f"Raw: {response.text[:300]}")

if __name__ == "__main__":
    test_feature_extraction()
    test_dedicated_endpoint()
    test_huggingface_hub()
    test_text_embeddings_inference()
