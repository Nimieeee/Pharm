
import os
import requests
import json

MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    print("MISTRAL_API_KEY not found")
    exit(1)

text_to_translate = "![A cross section of a human heart](http://15.237.208.231/api/v1/ai/image-proxy?prompt=human%20heart)"
source_name = "English"
target_name = "French"

messages = [
    {
        "role": "system",
        "content": f"You are a professional translator. Translate the following text from {source_name} to {target_name}. Preserve all formatting, markdown, and special characters. Only output the translation, nothing else."
    },
    {
        "role": "user", 
        "content": text_to_translate
    }
]

response = requests.post(
    "https://api.mistral.ai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "mistral-large-latest",
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 8000
    }
)

print(f"Status: {response.status_code}")
print(f"Output: {response.json()['choices'][0]['message']['content']}")
