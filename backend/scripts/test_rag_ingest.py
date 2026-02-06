
import asyncio
import os
import sys
import logging
from uuid import uuid4

# Setup paths
sys.path.append("/var/www/pharmgpt-backend/backend")

# Setup manual logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv("/var/www/pharmgpt-backend/.env")

from app.core.database import get_db as get_db_client
from app.services.enhanced_rag import EnhancedRAGService

async def test_manual_ingestion():
    print("🚀 Starting manual ingestion test...")
    
    # 1. Setup Service
    db = get_db_client()
    rag_service = EnhancedRAGService(db)
    
    # 2. Mock Data
    conv_id = uuid4()
    user_id = uuid4() #"8e4492fa-2a9a-4cb6-babd-a2ebc26fd269" # Existing user from logs
    filename = "manual_test_doc.txt"
    content = b"This is a test document for manual ingestion debugging. It contains vital pharmacology data."
    
    print(f"📄 Processing {filename} ({len(content)} bytes)...")
    
    # 3. Call Service
    try:
        result = await rag_service.process_uploaded_file(
            file_content=content,
            filename=filename,
            conversation_id=conv_id,
            user_id=user_id,
            mode="fast"
        )
        
        print(f"✅ Result: success={result.success}, chunks={result.chunk_count}, msg={result.message}")
        
        if result.success and result.chunk_count > 0:
            print("🎉 Success! Service layer is working.")
        else:
            print("❌ Failure! Service layer returned 0 chunks or error.")
            
    except Exception as e:
        print(f"💥 Exception during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_manual_ingestion())
