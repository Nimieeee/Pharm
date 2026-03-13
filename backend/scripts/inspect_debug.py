import asyncio
import os
import sys
from uuid import UUID

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import get_db
from app.services.chat import ChatService
from app.models.user import User

async def inspect():
    try:
        # Mock user (id doesn't matter for getting messages if we use service method that allows it, 
        # but ChatService usually requires user match. I'll use direct DB or bypass)
        # Actually ChatService.get_conversation_with_messages needs user.
        # I will just use Supabase client directly.
        from app.core.config import settings
        from supabase import create_client
        import os
        from dotenv import load_dotenv
        
        load_dotenv("pharmgpt-backend.env")
        
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
        
        if not url or not key:
            print("Missing Supabase credentials in env")
            return

        supabase = create_client(url, key)
        
        # Fetch latest conversation
        print("Fetching latest conversation...")
        conversations = supabase.table("conversations").select("id, title, updated_at").order("updated_at", desc=True).limit(1).execute()
        if not conversations.data:
            print("No conversations found.")
            return

        convo_id = conversations.data[0]["id"]
        title = conversations.data[0]["title"]
        print(f"Checking latest conversation: {convo_id} ({title})")
        
        print(f"Fetching messages for {convo_id}...")
        
        # Query messages
        response = supabase.table("messages").select("*").eq("conversation_id", convo_id).order("created_at").execute()
        
        messages = response.data
        print(f"Found {len(messages)} messages.")
        
        for msg in messages:
            print(f"[{msg['role']}] {msg['created_at']}")
            print(f"Content Preview: {msg['content'][:100]}...")
            print(f"Translations: {msg.get('translations')}")
            print(f"Metadata: {msg.get('metadata')}")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
