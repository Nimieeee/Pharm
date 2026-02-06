import asyncio
import os
import sys
from dotenv import load_dotenv
from uuid import uuid4

# Setup paths and env
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv("pharmgpt-backend.env")

from app.services.ai import AIService
from app.core.database import SessionLocal
from app.models.user import User

async def debug_stream():
    db = SessionLocal()
    ai_service = AIService(db)
    
    # Mock user
    user = User(id=uuid4(), email="test@example.com", first_name="DebugUser", language="en")
    
    print("--- SIMULATING 'hi' REQUEST ---")
    
    # Create a mock conversation ID (or use the real one if we want DB context)
    convo_id = uuid4() 
    
    # We want to see the LOGS printed by ai.py
    print("Calling generate_streaming_response...")
    
    async for chunk in ai_service.generate_streaming_response(
        message="hi",
        conversation_id=convo_id,
        user=user,
        mode="detailed", 
        language_override="en"
    ):
        # Consume stream to trigger logs
        pass
        
    print("\n--- SIMULATION COMPLETE ---")

if __name__ == "__main__":
    asyncio.run(debug_stream())
