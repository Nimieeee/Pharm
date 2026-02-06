import sys
import os
import asyncio
import logging
from dotenv import load_dotenv

sys.path.append(os.getcwd())
load_dotenv(".env")
logging.basicConfig(level=logging.INFO)

async def check_schema():
    print("🔍 Checking Database Schema...")
    from app.core.database import get_db
    
    client = get_db()
    
    # Query Postgres information schema to get column details
    try:
        # Note: This RPC call depends on if we have a function to exec SQL or if we can query schema tables via Supabase
        # Supabase-py doesn't allow raw SQL usually.
        # But we can try to insert a dummy vector of size 768 and see if it fails
        # AND insert a dummy vector of size 1024 and see if it fails.
        
        print("🧪 Testing 768-dim insertion...")
        dummy_768 = [0.1] * 768
        try:
            client.table("document_chunks").insert({
                "conversation_id": "00000000-0000-0000-0000-000000000000", # Dummy UUID
                "user_id": "00000000-0000-0000-0000-000000000000",
                "content": "schema_test_768",
                "embedding": dummy_768,
                "metadata": {"test": True}
            }).execute()
            print("✅ 768-dim insertion SUCCESS (DB is 768)")
            # Clean up
            client.table("document_chunks").delete().eq("content", "schema_test_768").execute()
        except Exception as e:
            print(f"❌ 768-dim insertion FAILED: {e}")

        print("🧪 Testing 1024-dim insertion...")
        dummy_1024 = [0.1] * 1024
        try:
            client.table("document_chunks").insert({
                "conversation_id": "00000000-0000-0000-0000-000000000000",
                "user_id": "00000000-0000-0000-0000-000000000000",
                "content": "schema_test_1024",
                "embedding": dummy_1024,
                "metadata": {"test": True}
            }).execute()
            print("✅ 1024-dim insertion SUCCESS (DB is 1024)")
            client.table("document_chunks").delete().eq("content", "schema_test_1024").execute()
        except Exception as e:
            print(f"❌ 1024-dim insertion FAILED: {e}")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())
