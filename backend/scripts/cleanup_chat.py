import asyncio
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load env
load_dotenv("pharmgpt-backend.env")
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

if not url or not key:
    print("Error: Missing credentials")
    sys.exit(1)

supabase = create_client(url, key)

async def cleanup():
    convo_id = "5e836804-ea80-4988-82f1-983412a83f1f"
    
    print(f"Cleaning conversation {convo_id}...")
    
    # Delete 'No response generated' messages
    print("Deleting 'No response generated' messages...")
    res = supabase.table("messages").delete().eq("conversation_id", convo_id).eq("content", "No response generated.").execute()
    print(f"Deleted {len(res.data) if res.data else 0} assistant messages.")
    
    # Delete duplicate user messages (content='make this into a presentation slide...')
    # We want to keep the LATEST one or just delete all and let user ask again.
    # To be safe, I'll delete ALL 'make this into...' messages so the user can start fresh from the report.
    print("Deleting user retry messages...")
    res = supabase.table("messages").delete().eq("conversation_id", convo_id).ilike("content", "make this into a presentation slide%").execute()
    print(f"Deleted {len(res.data) if res.data else 0} user messages.")
    
    print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(cleanup())
