import sys
import os
import asyncio
import uuid
import logging
from dotenv import load_dotenv
from datetime import datetime

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

# Load environment variables
load_dotenv(".env")

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_rag_e2e():
    try:
        print("\n🔎 Starting Verification: End-to-End RAG Chat Test")
        print("==================================================")
        
        # Import after path setup and env load
        from app.core.database import get_db
        from app.services.enhanced_rag import EnhancedRAGService
        from app.services.ai import AIService
        from app.models.user import User
        
        db = get_db()
        rag_service = EnhancedRAGService(db)
        ai_service = AIService(db)
        
        print("✅ Services Initialized")
        
        # Configuration
        user_uuid_str = "bef05b9e-7f4a-422f-8f77-c88af779e9aa"
        user_id = uuid.UUID(user_uuid_str)
        conversation_id = uuid.uuid4()
        
        # Mock User Object for AIService
        class MockUser:
            id = user_id
            first_name = "TestUser"
            language = "en"
        
        mock_user = MockUser()
        
        # 1. CREATE CONVERSATION
        print(f"\n1. Creating test conversation: {conversation_id}...")
        try:
            db.table("conversations").insert({
                "id": str(conversation_id),
                "user_id": str(user_id),
                "title": "Verification Test Chat",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            print("✅ Conversation created")
        except Exception as e:
            print(f"❌ Failed to create conversation: {e}")
            return

        # 2. UPLOAD DOCUMENT
        file_path = "tolu-result.docx"
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return

        print(f"\n2. Uploading {file_path}...")
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        result = await rag_service.process_uploaded_file(
            file_content=file_content,
            filename="tolu-result.docx",
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if not result.success:
            print(f"❌ Upload Failed: {result.message}")
            return
            
        print(f"✅ Upload Success: {result.chunk_count} chunks stored.")

        # 3. TEST RETRIEVAL & ANSWER
        query = "Summarize the charts and visual data in this document."
        print(f"\n3. Asking AI: '{query}'")
        
        response = await ai_service.generate_response(
            message=query,
            conversation_id=conversation_id,
            user=mock_user,
            mode="detailed",
            use_rag=True
        )
        
        print("\n🤖 AI Response:")
        print("--------------------------------------------------")
        print(response)
        print("--------------------------------------------------")
        
        if "No documents found" in response or "I cannot access" in response:
             print("❌ VERIFICATION FAILED: AI did not use RAG context.")
        else:
             print("\n✅ VERIFICATION PASSED: Answer generated!")

        # 4. CLEANUP
        print(f"\n4. Cleaning up conversation {conversation_id}...")
        db.table("conversations").delete().eq("id", str(conversation_id)).execute()
        print("✅ Cleanup complete.")

    except Exception as e:
        print(f"❌ CRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_rag_e2e())
