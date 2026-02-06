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

async def probe_real_content():
    print("🔬 Starting REAL CONTENT PROBE...")
    
    from app.core.database import get_db
    from app.services.document_loaders import EnhancedDocumentLoader
    from app.services.enhanced_rag import EnhancedRAGService
    
    # MONKEYPATCH TO DEBUG SERVICE
    original_method = EnhancedRAGService._process_and_store_chunk
    
    async def debug_wrapper(self, chunk, filename, conversation_id, user_id, chunk_index):
        print(f"🔥🔥 MONKEYPATCH: Chunk {chunk_index}")
        print(f"   - Content: {repr(chunk.page_content[:50])}...")
        print(f"   - Content Len: {len(chunk.page_content)}")
        
        # Call original
        # Note: original_method is unbound function if retrieved from class? 
        # No, async def on class. 
        # When called on instance `self` is passed.
        # But here we replace the CLASS method.
        try:
            res = await original_method(self, chunk, filename, conversation_id, user_id, chunk_index)
            print(f"🔥🔥 MONKEYPATCH Result: {res}")
            return res
        except Exception as e:
            print(f"🔥🔥 MONKEYPATCH Exception: {e}")
            raise

    EnhancedRAGService._process_and_store_chunk = debug_wrapper
    
    client = get_db()
    
    # 2. Extract Data
    file_path = "tolu-result.docx"
    if not os.path.exists(file_path):
        print("❌ File not found")
        return

    print("📄 extracting content...")
    loader = EnhancedDocumentLoader()
    # Mocking UploadFile-like object or reading bytes
    with open(file_path, "rb") as f:
        content_bytes = f.read()
    
    # We need to simulate how EnhancedRAG calls it
    # It calls smart_loader actually. 
    # But let's try DocumentLoader.load_document
    # It expects file_path usually or bytes?
    # EnhancedRAG calls:
    # docs = await self.document_loader.load_document(file_content, filename, user_id)
    
    # Wait, EnhancedRAG imports `documentloader` which uses `SmartLoader` internally if configured
    
    user_id = uuid.UUID("bef05b9e-7f4a-422f-8f77-c88af779e9aa")
    conversation_id = uuid.uuid4()
    
    try:
        docs = await loader.load_document(
            file_content=content_bytes,
            filename="tolu-result.docx",
            additional_metadata={"user_id": str(user_id)}
        )
    except Exception as e:
        print(f"❌ Extraction Error: {e}")
        return
        
    if not docs:
        print("❌ No docs extracted")
        return
        
    extracted_text = docs[0].page_content
    print(f"📄 Extracted {len(extracted_text)} chars")
    print(f"📄 START OF TEXT: {repr(extracted_text[:100])}")
    print(f"📄 END OF TEXT: {repr(extracted_text[-100:])}")
    
    # 3. Create Conversation
    try:
        client.table("conversations").insert({
            "id": str(conversation_id),
            "user_id": str(user_id),
            "title": "Real Content Probe",
            "created_at": "2024-01-01T00:00:00Z"
        }).execute()
        print("✅ Conversation created.")
    except Exception as e:
        print(f"❌ Failed to create conversation: {e}")
        return

    # 4. Generate Data
    # USE REAL EMBEDDING SERVICE
    print("🧠 Generating Real Embedding via Mistral...")
    from app.services.embeddings import embeddings_service
    embedding = await embeddings_service.generate_embedding(extracted_text)
    
    if not embedding:
        print("❌ Failed to generate embedding!")
        return
        
    print(f"🧠 Generated embedding length: {len(embedding)}")
    
    # Check for NaN/Inf
    import math
    if any(math.isnan(x) for x in embedding) or any(math.isinf(x) for x in embedding):
        print("❌ Embedding contains NaN or Inf!")
        return
    
    data = {
        "conversation_id": str(conversation_id),
        "user_id": str(user_id),
        "content": extracted_text, # THE REAL CONTENT
        "embedding": embedding,
        "metadata": docs[0].metadata
    }
    
    print(f"Attempting insertion with extracted text...")
    
    # 5. Direct Insert
    try:
        response = client.table("document_chunks").insert(data).execute()
        
        print("\n📝 RAW RESPONSE:")
        print(response)
        
        if response.data:
            print("✅ INSERT SUCCESS!")
            # cleanup
            client.table("document_chunks").delete().eq("content", extracted_text).execute()
        else:
            print("❌ INSERT FAILED (Empty Data)")
            if hasattr(response, 'error'):
                 print(f"ERROR: {response.error}")
            
    except Exception as e:
        print(f"❌ EXCEPTION DURING INSERT: {e}")

    
    # 6. NOW CALL THE SERVICE TO TEST MONKEYPATCH
    print("\n🔥🔥 TELEMETRY: Calling Service via Monkeypatch...")
    rag_service = EnhancedRAGService(client)
    
    # We need to recreate the file content bytes
    # content_bytes is available from earlier
    
    try:
        res = await rag_service.process_uploaded_file(
            file_content=content_bytes,
            filename="tolu-result.docx",
            conversation_id=conversation_id,
            user_id=user_id
        )
        print(f"🔥🔥 SERVICE CALL FINISHED. Result: {res}")
    except Exception as e:
        print(f"🔥🔥 SERVICE CALL EXCEPTION: {e}")

    # Cleanup Conversation
    try:
        client.table("conversations").delete().eq("id", str(conversation_id)).execute()
    except:
        pass

if __name__ == "__main__":
    asyncio.run(probe_real_content())
