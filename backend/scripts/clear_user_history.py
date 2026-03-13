import asyncio
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import db
from app.services.auth import AuthService

async def clear_history():
    email = "odunewutolu2@gmail.com"
    print(f"Finding user {email}...")
    
    auth = AuthService(db.get_client())
    user = await auth.get_user_by_email(email)
    
    if not user:
        print(f"User {email} not found.")
        return
        
    print(f"Found user ID: {user.id}")
    
    # Supabase cascade delete handles messages automatically if set up, 
    # but we can just use the db client to delete directly to be safe
    client = db.get_client()
    
    # Delete conversations - this should cascade to messages if foreign keys are setup correctly
    print("Deleting conversations...")
    res = client.table("conversations").delete().eq("user_id", str(user.id)).execute()
    print(f"Deleted conversations.")
    
    # Delete messages just in case cascade is not on
    print("Deleting messages...")
    res = client.table("messages").delete().eq("user_id", str(user.id)).execute()
    print(f"Deleted messages.")
    
    print("History cleared successfully.")

if __name__ == "__main__":
    asyncio.run(clear_history())
