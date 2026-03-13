
import os
import asyncio
from supabase import create_client, Client
from dotenv import load_dotenv

# Load env variables from the backend file
load_dotenv("pharmgpt-backend.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") # Use Service Role to bypass RLS

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing Supabase credentials")
    exit(1)

async def check_conversations():
    print(f"Connecting to Supabase at {SUPABASE_URL}...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Check total conversations
    try:
        response = supabase.table("conversations").select("id, user_id, title, created_at").order("created_at", desc=True).limit(10).execute()
        conversations = response.data
        
        print(f"\n📊 Total Conversations Found: {len(conversations)}")
        
        if not conversations:
            print("⚠️ The 'conversations' table is empty.")
        else:
            print("\nRecent Conversations:")
            for c in conversations:
                print(f" - ID: {c['id']}")
                print(f"   User: {c['user_id']}")
                print(f"   Title: {c['title']}")
                print(f"   Created: {c['created_at']}")
                print("-" * 30)
                
    except Exception as e:
        print(f"❌ Error querying database: {e}")

if __name__ == "__main__":
    asyncio.run(check_conversations())
