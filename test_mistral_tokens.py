import asyncio
import httpx

async def run():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://api.mistral.ai/v1/chat/completions',
            headers={'Authorization': 'Bearer uBrKHYN5sBzrvdTYgel7zyNuPVbnhijv'},
            json={
                'model': 'mistral-large-latest',
                'messages': [{'role': 'user', 'content': 'Count to 10'}],
                'max_tokens': 32000
            }
        )
        print(response.status_code)
        
        # If max_tokens 32000 is too large, let's try 16000
        if response.status_code != 200:
             response = await client.post(
                'https://api.mistral.ai/v1/chat/completions',
                headers={'Authorization': 'Bearer uBrKHYN5sBzrvdTYgel7zyNuPVbnhijv'},
                json={
                    'model': 'mistral-large-latest',
                    'messages': [{'role': 'user', 'content': 'Count to 10'}],
                    'max_tokens': 16000
                }
            )
             print('16k:', response.status_code)

asyncio.run(run())
