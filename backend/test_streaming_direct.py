#!/usr/bin/env python3
"""
Direct test of the streaming endpoint to diagnose the hang issue
"""
import asyncio
import httpx
import json
import sys

async def test_streaming():
    """Test the streaming endpoint directly"""
    
    # Replace with actual values
    API_URL = "https://benchside.com/api/v1/ai/chat/stream"
    TOKEN = input("Enter your auth token: ").strip()
    CONVERSATION_ID = input("Enter conversation ID: ").strip()
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "conversation_id": CONVERSATION_ID,
        "message": "explain well",
        "mode": "fast",
        "use_rag": True,
        "language": "en",
        "metadata": {}
    }
    
    print("\n" + "="*60)
    print("Testing Streaming Endpoint")
    print("="*60)
    print(f"URL: {API_URL}")
    print(f"Conversation: {CONVERSATION_ID}")
    print(f"Message: {payload['message']}")
    print("="*60 + "\n")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("📡 Sending request...")
            
            async with client.stream(
                "POST",
                API_URL,
                headers=headers,
                json=payload
            ) as response:
                print(f"✅ Response status: {response.status_code}")
                print(f"📋 Headers: {dict(response.headers)}\n")
                
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"❌ Error: {error_text.decode()}")
                    return
                
                print("📥 Receiving stream...\n")
                print("-" * 60)
                
                chunk_count = 0
                start_time = asyncio.get_event_loop().time()
                last_chunk_time = start_time
                
                async for line in response.aiter_lines():
                    current_time = asyncio.get_event_loop().time()
                    time_since_start = current_time - start_time
                    time_since_last = current_time - last_chunk_time
                    
                    if line.strip():
                        chunk_count += 1
                        print(f"[{time_since_start:.2f}s | +{time_since_last:.2f}s] Chunk #{chunk_count}:")
                        print(f"  {line[:200]}")  # Print first 200 chars
                        
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                print("\n✅ Stream completed successfully!")
                                break
                            try:
                                parsed = json.loads(data)
                                if "text" in parsed:
                                    print(f"  Text: {parsed['text'][:100]}...")
                                elif "type" in parsed:
                                    print(f"  Meta: {parsed}")
                            except json.JSONDecodeError:
                                pass
                        
                        last_chunk_time = current_time
                
                total_time = asyncio.get_event_loop().time() - start_time
                print("-" * 60)
                print(f"\n📊 Summary:")
                print(f"  Total chunks: {chunk_count}")
                print(f"  Total time: {total_time:.2f}s")
                print(f"  Avg time per chunk: {total_time/chunk_count if chunk_count > 0 else 0:.2f}s")
                
                if chunk_count == 0:
                    print("\n❌ NO CHUNKS RECEIVED - Stream is hanging!")
                    print("   This confirms the frontend issue.")
                
    except httpx.TimeoutException:
        print("\n❌ Request timed out!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming())
