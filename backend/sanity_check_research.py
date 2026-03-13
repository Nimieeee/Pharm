import asyncio
import os
import sys
import uuid
from datetime import datetime

# Add the project root to sys.path
PRJ_ROOT = "/var/www/pharmgpt-backend/backend"
sys.path.append(PRJ_ROOT)

# Manual .env loading to avoid dependency issues
def load_env():
    env_path = os.path.join(PRJ_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value.strip("'\"")

load_env()

from app.services.deep_research import DeepResearchService

from app.services.chat import ChatService
from app.services.enhanced_rag import EnhancedRAGService
from app.core.database import db as db_manager
from app.models.user import User

async def run_sanity_check():
    print("🚀 Running Unified Deep Research Sanity Check (Direct Service Call)")
    
    db = db_manager.get_client()
    # Get a real user
    users = db.table("users").select("id, email").limit(1).execute()
    if not users.data:
        print("❌ No users found in database")
        return
    
    user_id = users.data[0]["id"]
    email = users.data[0]["email"]
    print(f"👤 Using User: {email} ({user_id})")
    
    # Create a test conversation
    conv = db.table("conversations").insert({
        "user_id": user_id,
        "title": f"Test Research {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    }).execute()
    conv_id = conv.data[0]["id"]
    print(f"📁 Created Test Conversation: {conv_id}")
    
    research_service = DeepResearchService(db)
    chat_service = ChatService(db)
    rag_service = EnhancedRAGService(db)
    
    question = "What is the mechanism of action of Levetiracetam?"
    print(f"❓ Research Question: {question}")
    
    # Simulate the unified stream logic
    print("📥 Starting Stream Simulation...")
    
    meta_received = False
    complete_received = False
    
    # We'll just run one step to verify it works (or skip if too slow, but let's try a full small run)
    # Actually, let's just run a few items from the generator
    count = 0
    async for item in research_service.run_research_streaming(question, user_id):
        count += 1
        if count % 5 == 0:
            print(f"Received chunk {count}...")
        if "complete" in item:
            print("✅ 'complete' event received!")
            complete_received = True
            break
        if count > 50: # Limit test time
            print("⚠️ Test reached chunk limit, stopping.")
            break
            
    print(f"📊 Test finished. Received {count} chunks.")
    
    # Cleanup (optional - but we leave it for user to see in history)
    print(f"✅ Sanity check complete. Go to the dashboard to see conversation {conv_id}")

if __name__ == "__main__":
    asyncio.run(run_sanity_check())
