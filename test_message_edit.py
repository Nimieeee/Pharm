"""
Test script to reproduce the message edit 500 error
"""
import os
import sys
import asyncio
from uuid import UUID

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from supabase import create_client
from app.core.config import settings

async def test_message_edit():
    """Test updating a message"""
    
    # Initialize Supabase client
    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY or settings.SUPABASE_ANON_KEY
    
    print(f"Connecting to Supabase: {supabase_url[:30]}...")
    
    try:
        client = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Test message ID from the error
    test_message_id = "682dd5d0-1cdd-44a3-9202-0dd0456c0e52"
    
    # First, fetch the message to see its structure
    print(f"\n📋 Fetching message {test_message_id}...")
    try:
        result = client.table("messages").select("*").eq("id", test_message_id).execute()
        if result.data:
            msg = result.data[0]
            print(f"✅ Found message:")
            print(f"   - Role: {msg.get('role')}")
            print(f"   - User ID: {msg.get('user_id')}")
            print(f"   - Conversation ID: {msg.get('conversation_id')}")
            print(f"   - Content (first 100 chars): {msg.get('content', '')[:100]}...")
        else:
            print(f"❌ Message not found")
            return
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return
    
    # Try to update the message
    print(f"\n✏️  Attempting to update message...")
    try:
        update_data = {"content": "[TEST] Updated content"}
        result = client.table("messages").update(update_data).eq("id", test_message_id).execute()
        
        if result.data:
            print(f"✅ Update successful!")
            print(f"   - Updated content: {result.data[0].get('content', '')[:50]}...")
        else:
            print(f"❌ Update returned no data")
            print(f"   - Result: {result}")
    except Exception as e:
        print(f"❌ Update failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with user_id filter (mimicking the actual endpoint)
    print(f"\n✏️  Attempting to update with user_id filter...")
    try:
        user_id = msg.get('user_id')
        update_data = {"content": "[TEST] Updated content with user filter"}
        result = client.table("messages").update(update_data).eq("id", test_message_id).eq("user_id", user_id).execute()
        
        if result.data:
            print(f"✅ Update with user_id successful!")
        else:
            print(f"❌ Update with user_id returned no data")
            print(f"   - Result: {result}")
            print(f"   - This might indicate RLS policy issue")
    except Exception as e:
        print(f"❌ Update with user_id failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_message_edit())
