import asyncio
import os
import sys

# Add backend directory to path
sys.path.append(os.getcwd())

from app.core.database import init_db, db

async def check():
    print("Checking translation progress...")
    await init_db()
    
    try:
        # Check messages
        total_msgs = db.get_client().table("messages").select("id", count="exact").execute()
        msgs_done = db.get_client().table("messages").select("id", count="exact").not_.is_("translations", "null").execute()
        
        total_m = total_msgs.count
        done_m = msgs_done.count
        rem_m = total_m - done_m
        
        # Check conversations
        total_convs = db.get_client().table("conversations").select("id", count="exact").execute()
        convs_done = db.get_client().table("conversations").select("id", count="exact").not_.is_("title_translations", "null").execute()
        
        total_c = total_convs.count
        done_c = convs_done.count
        rem_c = total_c - done_c
        
        print(f"📊 Progress Report:")
        print(f"   - Messages:      {done_m} / {total_m} done ({rem_m} remaining)")
        print(f"   - Conversations: {done_c} / {total_c} done ({rem_c} remaining)")
        
    except Exception as e:
        print(f"❌ Error checking progress: {e}")

if __name__ == "__main__":
    asyncio.run(check())
