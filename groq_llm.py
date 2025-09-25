# groq_llm.py

from groq import Groq

# Initialize Groq client (API key auto-loaded from env: GROQ_API_KEY)
client = Groq()

# Define modes
FAST_MODE = "gemma-7b-it"          # fast, lightweight
PREMIUM_MODE = "openai/gpt-oss-20b"  # powerful, larger

def generate_completion(messages, model=FAST_MODE, temperature=0.7, max_tokens=1024):
    """
    Single-response generation (no streaming).
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens,
        top_p=1,
    )
    return response.choices[0].message.content


def generate_completion_stream(messages, model=FAST_MODE, temperature=0.7, max_tokens=1024):
    """
    Streaming response generation (yields tokens).
    """
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_completion_tokens=max_tokens,
        top_p=1,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
