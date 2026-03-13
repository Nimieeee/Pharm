import sys
import os
import asyncio
import uuid
import logging
import random
import time
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv(".env")

logging.basicConfig(level=logging.INFO)

async def probe_full_payload():
    print("🔬 Starting FULL PAYLOAD PROBE...")
    
    from app.core.database import get_db
    from app.core.config import settings
    
    client = get_db()
    
    # 2. Prepare Data
    user_id = "bef05b9e-7f4a-422f-8f77-c88af779e9aa"
    conversation_id = str(uuid.uuid4())
    
    # 3. Create Conversation
    try:
        client.table("conversations").insert({
            "id": conversation_id,
            "user_id": user_id,
            "title": "Full Payload Probe",
            "created_at": "2024-01-01T00:00:00Z"
        }).execute()
        print("✅ Conversation created.")
    except Exception as e:
        print(f"❌ Failed to create conversation: {e}")
        return

    # 4. Generate Data
    vector = [random.random() for _ in range(1024)]
    
    # Simulate the metadata from EnhancedRAGService
    metadata = {
        "file_type": "docx",
        "file_path": "/tmp/tolu-result.docx",
        "filename": "tolu-result.docx",
        "user_id": str(user_id),
        "conversation_id": str(conversation_id),
        "embedding_model": "mistral",
        "embedding_dimensions": 1024,
        "processing_timestamp": time.time(),
        "chunk_length": 192,
        "langchain_processed": True
    }
    
    # Simulate content
    content = "This is a test content string to verify insertion."
    
    data = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "content": content,
        "embedding": vector,
        "metadata": metadata
    }
    
    print(f"Attempting insertion with complex metadata...")
    print(f"Metadata: {metadata}")
    
    # 5. Direct Insert
    try:
        response = client.table("document_chunks").insert(data).execute()
        
        print("\n📝 RAW RESPONSE:")
        print(response)
        
        if response.data:
            print("✅ INSERT SUCCESS!")
            # Cleanup
            client.table("document_chunks").delete().eq("content", content).execute()
        else:
            print("❌ INSERT FAILED (Empty Data)")
            if hasattr(response, 'error'):
                 print(f"ERROR: {response.error}")
            
    except Exception as e:
        print(f"❌ EXCEPTION DURING INSERT: {e}")
            
    # Cleanup Conversation
    try:
        client.table("conversations").delete().eq("id", conversation_id).execute()
        print("✅ Conversation cleanup done.")
    except:
        pass

if __name__ == "__main__":
    asyncio.run(probe_full_payload())
