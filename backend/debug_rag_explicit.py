import sys
import os
print("🔥🔥 FIRE START: Script beginning")
sys.stdout.flush()

import asyncio
import uuid
import logging
import inspect
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv(".env")

# Configure logging
logging.basicConfig(level=logging.DEBUG)
print("🔥🔥 LOGGING CONFIGURED")

async def reproduce():
    print("🔥🔥 ASYNC START")
    try:
        from app.core.database import get_db
        from app.services.enhanced_rag import EnhancedRAGService
        
        print(f"🔥🔥 MODULE PATH: {inspect.getfile(EnhancedRAGService)}")
        
        db = get_db()
        rag_service = EnhancedRAGService(db)
        
        # Manually invoke the method to verify my monkeypatch/edit status
        # We'll use a dummy chunk
        print("🔥🔥 PREPARING DUMMY CHUNK")
        
        user_id = uuid.UUID("bef05b9e-7f4a-422f-8f77-c88af779e9aa")
        conversation_id = uuid.uuid4()
        
        # Insert Conversation
        try:
            db.table("conversations").insert({
                "id": str(conversation_id),
                "user_id": str(user_id),
                "title": "FIRE TEST",
                "created_at": "2024-01-01T00:00:00Z"
            }).execute()
            print("🔥🔥 CONVERSATION CREATED")
        except Exception as e:
            print(f"🔥🔥 CONVERSATION ERROR: {e}")
            return

        # Prepare payload manually to see if WE can insert 1024 dims
        # This matches what EnhancedRAGService does, but we control it
        import random
        embedding = [random.random() for _ in range(1024)]
        
        chunk_data = {
            "conversation_id": str(conversation_id),
            "user_id": str(user_id),
            "content": "FIRE TEST CONTENT",
            "embedding": embedding,
            "metadata": {"source": "fire_test"}
        }
        
        print(f"🔥🔥 ATTEMPTING DIRECT INSERT OF 1024 DIMS")
        result = db.table("document_chunks").insert(chunk_data).execute()
        print(f"🔥🔥 DIRECT INSERT RESULT: {result}")
        
        # Now try via Service
        print("🔥🔥 CALLING SERVICE process_uploaded_file")
        # We need a dummy file content
        file_content = b"This is a fire test document."
        
        res = await rag_service.process_uploaded_file(
            file_content=file_content,
            filename="fire_test.txt",
            conversation_id=conversation_id,
            user_id=user_id
        )
        print(f"🔥🔥 SERVICE RESULT: {res}")
        
        # Cleanup
        db.table("conversations").delete().eq("id", str(conversation_id)).execute()
        
    except Exception as e:
        print(f"🔥🔥 EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())
