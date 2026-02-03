import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path so we can import app modules
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.core.database import db, init_db
from app.services.translation_service import TranslationService

async def backfill_translations():
    print("🚀 Starting Translation Backfill...")
    
    # Initialize DB connection
    await init_db()
    
    translation_service = TranslationService(db.get_client())
    
    # 1. Backfill Messages
    print("\n📦 Checking Messages...")
    try:
        # Fetch messages directly using Supabase client
        # Note: "is" null syntax might vary depending on client, usually .is_("translations", "null")
        response = db.get_client().table("messages").select("id, content, role").is_("translations", "null").execute()
        messages = response.data
        
        print(f"Found {len(messages)} messages needing translation.")
        
        for i, msg in enumerate(messages):
            if not msg.get("content"):
                continue
                
            print(f"Processing message {i+1}/{len(messages)}: {msg['id']}")
            
            try:
                # Default source is 'en' for now, or infer? 
                # Ideally we'd store source language, but for backfill 'en' is safest guess for old data
                await translation_service._translate_and_store_message(
                    message_id=msg['id'],
                    content=msg['content'],
                    source_language='en' 
                )
                # Sleep reduced as Kimi/Mistral has higher throughput
                # await asyncio.sleep(0.5) 
                
            except Exception as e:
                print(f"Failed to process message {msg['id']}: {e}")
                
    except Exception as e:
        print(f"❌ Error querying messages (maybe column missing?): {e}")

    # 2. Backfill Conversations (Titles)
    print("\n🗂️ Checking Conversations...")
    try:
        response = db.get_client().table("conversations").select("id, title").is_("title_translations", "null").execute()
        conversations = response.data
        
        print(f"Found {len(conversations)} conversations needing title translation.")
        
        for i, conv in enumerate(conversations):
            if not conv.get("title"):
                continue
                
            print(f"Processing conversation {i+1}/{len(conversations)}: {conv['id']}")
            
            try:
                await translation_service._translate_and_store_title(
                    conversation_id=conv['id'],
                    title=conv['title'],
                    source_language='en'
                )
                # await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"Failed to process conversation {conv['id']}: {e}")
                
    except Exception as e:
        print(f"❌ Error querying conversations: {e}")

    print("\n✅ Backfill Complete!")

if __name__ == "__main__":
    asyncio.run(backfill_translations())
