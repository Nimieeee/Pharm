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
        print("🚀 Starting VPS RAG Reproduction...")
        
        # Import after path setup and env load
        from app.core.database import get_db
        from app.services.enhanced_rag import EnhancedRAGService
        
        # Initialize Service
        rag_service = EnhancedRAGService(get_db())
        print("✅ EnhancedRAGService Initialized")
        
        # Configuration
        # Using a valid user ID found in logs/debug scripts
        user_id = uuid.UUID("bef05b9e-7f4a-422f-8f77-c88af779e9aa") 
        conversation_id = uuid.uuid4()
        # File is expected to be in the same directory on VPS
        file_path = "tolu-result.docx"
        
        if not os.path.exists(file_path):
            print(f"❌ File not found at {file_path}")
            print(f"CWD: {os.getcwd()}")
            print(f"Files: {os.listdir('.')}")
            return

        print(f"📄 Reading file: {file_path}")
        with open(file_path, "rb") as f:
            file_content = f.read()
            
        print(f"📦 File size: {len(file_content)} bytes")
        
        # Process File
        print("⚙️ Processing file...")
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
                print("Errors:")
                for err in result.errors:
                    print(f" - {err}")
    
    except Exception as e:
        print(f"❌ CRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())
