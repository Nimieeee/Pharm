import os
import requests

def check_mistral_rate_limit(api_key, model="mistral-small-latest"):
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5
    }
    print(f"\n--- Checking {model} ---")
    response = requests.post(url, headers=headers, json=data)
    
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error: {response.text}")
        
    print("Headers:")
    for key, value in response.headers.items():
        if "ratelimit" in key.lower():
            print(f"  {key}: {value}")
    print("\nAll headers:")
    for key, value in response.headers.items():
        print(f"  {key}: {value}")

api_key = "uBrKHYN5sBzrvdTYgel7zyNuPVbnhijv"
check_mistral_rate_limit(api_key, "mistral-small-latest")
check_mistral_rate_limit(api_key, "mistral-large-latest")
