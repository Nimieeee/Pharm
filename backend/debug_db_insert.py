import sys
import os
import asyncio
import uuid
import logging
import random
from dotenv import load_dotenv
from datetime import datetime

sys.path.append(os.getcwd())
load_dotenv(".env")
logging.basicConfig(level=logging.INFO)

async def probe_db():
    print("🔬 Starting Low-Level DB Probe (Fixed)...")
    
    from app.core.database import get_db
    from app.core.config import settings
    
    client = get_db()
    
    print(f"Configured Dimensions: {settings.EMBEDDING_DIMENSIONS}")
    
    # 2. Prepare Data
    user_id = "bef05b9e-7f4a-422f-8f77-c88af779e9aa"
    conversation_id = str(uuid.uuid4())
    
    # 3. Create Conversation FIRST
    print(f"Creating parent conversation {conversation_id}...")
    try:
        client.table("conversations").insert({
            "id": conversation_id,
            "user_id": user_id,
            "title": "Probe Test",
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        print("✅ Conversation created.")
    except Exception as e:
        print(f"❌ Failed to create conversation: {e}")
        return

    # 4. Generate Dummy 1024 Vector
    vector = [random.random() for _ in range(1024)]
    
    data = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "content": "TEST_PROBE_VECTOR_1024_FIXED",
        "embedding": vector,
        "metadata": {"source": "probe_script"}
    }
    
    print(f"Attempting insertion with {len(vector)} dims...")
    
    # 5. Direct Insert
    try:
        response = client.table("document_chunks").insert(data).execute()
        
        print("\n📝 RAW RESPONSE:")
        print(response)
        
        if response.data:
            print("✅ INSERT SUCCESS! (1024 Dims Confirmed)")
            # Cleanup
            print("Cleaning up...")
            client.table("document_chunks").delete().eq("content", "TEST_PROBE_VECTOR_1024_FIXED").execute()
        else:
            print("❌ INSERT FAILED (Empty Data)")
            
    except Exception as e:
        print(f"❌ EXCEPTION DURING INSERT: {e}")
        if hasattr(e, '__dict__'):
            print(e.__dict__)
            
    # Cleanup Conversation
    try:
        client.table("conversations").delete().eq("id", conversation_id).execute()
        print("✅ Conversation cleanup done.")
    except:
        pass

if __name__ == "__main__":
    asyncio.run(probe_db())
