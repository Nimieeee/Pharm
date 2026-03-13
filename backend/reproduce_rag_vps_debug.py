import sys
import os
import asyncio
import uuid
import logging
from dotenv import load_dotenv

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

# Load environment variables
load_dotenv(".env")

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reproduce():
    try:
        print("🚀 Starting VPS RAG Reproduction (Detailed Error Mode)...")
        
        # Import after path setup and env load
        from app.core.database import get_db
        from app.services.enhanced_rag import EnhancedRAGService
        
        # Initialize Service
        rag_service = EnhancedRAGService(get_db())
        print("✅ EnhancedRAGService Initialized")
        
        # Configuration
        user_id = uuid.UUID("bef05b9e-7f4a-422f-8f77-c88af779e9aa") 
        conversation_id = uuid.uuid4()
        file_path = "tolu-result.docx"
        
        if not os.path.exists(file_path):
            print(f"❌ File not found at {file_path}")
            return

        print(f"📄 Reading file: {file_path}")
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        print(f"📦 File size: {len(file_content)} bytes")
        
        # Process File
        print("⚙️ Processing file...")
        
        # We'll hook into the service to catch the low-level exception if possible
        # But for now, let's rely on the service to return errors in the response
        result = await rag_service.process_uploaded_file(
            file_content=file_content,
            filename="tolu-result.docx",
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        if result.success:
            print("✅ SUCCESS!")
            print(f"Message: {result.message}")
            print(f"Chunks: {result.chunk_count}")
        else:
            print("❌ FAILURE!")
            print(f"Message: {result.message}")
            if result.errors:
                print("Detailed Errors:")
                for err in result.errors:
                    print(f" - {err}")
            
            # Additional Check: PROBE THE LOG FILE for the specific error
            print("\n🔍 Recent Error Logs:")
            # We can't easily grep the log from python without os.system
            os.system("tail -n 20 ~/.pm2/logs/pharmgpt-backend-error.log")
    
    except Exception as e:
        print(f"❌ CRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())
